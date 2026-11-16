from io import BytesIO
import logging
import time
import os
import subprocess
import sys
from unittest.mock import patch
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import RequestDataTooBig
from django.test import Client, SimpleTestCase, override_settings
from .geometry import Candidate
from .imaging import decode, png
from .limits import AnalysisLimiter, limiter
from .logging import RedactResultURLs
from .responses import LANGUAGE_COOKIE, LEGACY_LANGUAGE_COOKIE
from .uploads import BoundedMemoryUploadHandler, MAX_FILE_BYTES


def uploaded():
    return SimpleUploadedFile('private-name.png', png(Image.new('RGB', (162, 100), 'white')), 'image/png')


@override_settings(DEBUG=True, ALLOWED_HOSTS=['localhost'])
class SecurityFlowTests(SimpleTestCase):
    def setUp(self):
        limiter.clear()
        self.client = Client(enforce_csrf_checks=True, HTTP_HOST='localhost')
        self.client.get('/')
        self.csrf = self.client.cookies['csrftoken'].value
        self.headers = {'HTTP_ACCEPT': 'application/json', 'HTTP_ORIGIN': 'http://localhost'}

    def post(self, path='/', **data):
        return self.client.post(path, {'csrfmiddlewaretoken': self.csrf, **data}, **self.headers)

    def test_single_screen_json_flow_and_localization(self):
        with patch('lab.views.analyze', return_value=[Candidate('frame', [[0, 0], [161, 0], [161, 99], [0, 99]], .5)]):
            response = self.post(image=uploaded())
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['ok'])
        self.assertIn('Encuadre', result['html'])
        self.assertNotIn('<script', result['html'])
        self.assertGreater(result['expires_in'], 0)
        token = result['token']
        locale = self.post('/language/', language='en', token=token)
        self.assertEqual(locale.json()['lang'], 'en')
        self.assertIn('Frame', locale.json()['html'])
        self.assertEqual(locale.json()['token'], token)
        self.assertTrue(locale.cookies[LANGUAGE_COOKIE]['httponly'])
        download = self.client.get(f'/image/{token}/download/')
        self.assertEqual(Image.open(BytesIO(download.content)).size, (162, 100))
        self.assertEqual(self.post(f'/delete/{token}/').json(), {'ok': True})
        expired = self.client.get(f'/result/{token}/', **self.headers)
        self.assertEqual(expired.status_code, 404)
        self.assertEqual(expired.json()['code'], 'expired')

    def test_csrf_failure_is_json_without_technical_reason(self):
        response = self.client.post('/language/', {'language': 'en'}, **self.headers)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['code'], 'csrf')
        self.assertNotIn('Reason given', response.content.decode())

    def test_header_body_limit(self):
        response = self.client.generic('POST', '/', b'', content_type='application/octet-stream',
                                       CONTENT_LENGTH=str(12 * 1024 * 1024), **self.headers)
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()['code'], 'size')
        self.assertIn('no-store', response['Cache-Control'])

    def test_streamed_file_limit(self):
        file = SimpleUploadedFile('oversized.png', b'x' * (MAX_FILE_BYTES + 1), 'image/png')
        response = self.post(image=file)
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()['code'], 'size')

    def test_only_one_file_and_bounded_fields(self):
        response = self.post(image=[uploaded(), uploaded()])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['code'], 'request_error')
        response = self.post('/language/', **{f'field{i}': 'x' for i in range(10)})
        self.assertEqual(response.status_code, 400)

    @override_settings(ANALYSIS_RATE_LIMIT=1)
    def test_rate_limit_prevents_second_expensive_analysis(self):
        with patch('lab.views.analyze', return_value=[]) as analyze:
            self.assertEqual(self.post(image=uploaded()).status_code, 200)
            limited = self.post(image=uploaded())
            self.assertEqual(limited.status_code, 429)
            self.assertEqual(limited.json()['code'], 'rate_limit')
            self.assertEqual(limited['Retry-After'], '60')
            self.assertEqual(analyze.call_count, 1)

    def test_processing_failure_is_generic_and_releases_slot(self):
        with patch('lab.views.analyze', side_effect=RuntimeError('private-name.png')):
            response = self.post(image=uploaded())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['code'], 'server_error')
        self.assertNotIn('private-name', response.content.decode())
        with patch('lab.views.analyze', return_value=[]):
            self.assertEqual(self.post(image=uploaded()).status_code, 200)

    def test_previous_language_choice_migrates_on_explicit_selection(self):
        self.client.cookies[LEGACY_LANGUAGE_COOKIE] = 'en'
        self.assertContains(self.client.get('/'), 'lang="en"')
        response = self.post('/language/', language='en')
        self.assertEqual(response.cookies[LANGUAGE_COOKIE].value, 'en')
        self.assertEqual(response.cookies[LEGACY_LANGUAGE_COOKIE]['max-age'], 0)

    def test_invalid_image_and_extreme_dimensions(self):
        self.assertEqual(self.post(image=SimpleUploadedFile('x.png', b'bad')).json()['code'], 'format')
        file = SimpleUploadedFile('panorama.png', png(Image.new('RGB', (12001, 32))), 'image/png')
        self.assertEqual(self.post(image=file).json()['code'], 'pixels')


class SecurityUnitTests(SimpleTestCase):
    def test_production_rejects_missing_and_weak_secrets(self):
        for secret in ('', 'replace-with-a-long-random-secret', 'a' * 60):
            environment = {**os.environ, 'DJANGO_DEBUG': '0', 'DJANGO_SECRET_KEY': secret}
            result = subprocess.run([sys.executable, '-c', 'import golden_ratio_tester.settings'],
                                    capture_output=True, text=True, env=environment)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('DJANGO_SECRET_KEY', result.stderr)

    def test_streaming_handler_caps_unknown_length(self):
        handler = BoundedMemoryUploadHandler()
        handler.new_file('image', 'test.png', 'image/png', None)
        with self.assertRaises(RequestDataTooBig):
            handler.receive_data_chunk(b'xx', MAX_FILE_BYTES - 1)
        self.assertTrue(handler.file.closed)

    def test_rate_storage_is_bounded_and_expires(self):
        guard = AnalysisLimiter(window=.02, capacity=2)
        self.assertTrue(guard.allow('client-a', 1))
        self.assertFalse(guard.allow('client-a', 1))
        guard.allow('client-b', 1); guard.allow('client-c', 1)
        self.assertEqual(len(guard.entries), 2)
        self.assertNotIn(b'client-b', guard.entries)
        time.sleep(.05)
        self.assertEqual(len(guard.entries), 0)
        self.assertTrue(guard.allow('client-b', 1))
        self.assertEqual(len(guard.entries), 1)

    def test_capability_urls_are_redacted_in_logs(self):
        record = logging.LogRecord('django.server', logging.INFO, __file__, 1,
                                   'GET /image/%s/download/ HTTP/1.1', ('secret-token',), None)
        RedactResultURLs().filter(record)
        self.assertNotIn('secret-token', record.getMessage())
        self.assertIn('/image/[private]/download/', record.getMessage())

    def test_exif_orientation_is_normalized_and_metadata_removed(self):
        source = Image.new('RGB', (80, 120), 'white')
        exif = Image.Exif(); exif[274] = 6; exif[270] = 'private description'
        buffer = BytesIO(); source.save(buffer, 'JPEG', exif=exif)
        result = decode(SimpleUploadedFile('photo.jpg', buffer.getvalue(), 'image/jpeg'))
        self.assertEqual(result.size, (120, 80))
        self.assertEqual(result.info, {})
