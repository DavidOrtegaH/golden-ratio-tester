from io import BytesIO
import math
import time
from unittest.mock import patch
import numpy as np
from PIL import Image, ImageDraw
from django.test import SimpleTestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from .copy import COPY
from .geometry import PHI, GROWTH, analyze, fit_spiral
from .imaging import decode, png
from .store import ResultStore


def upload(image):
    return SimpleUploadedFile('private.png', png(image), content_type='image/png')


def spiral_image(growth=GROWTH, mirrored=False):
    image = Image.new('RGB', (600, 600), 'white')
    t = np.linspace(0, 3 * math.pi, 1000)
    r = 12 * np.exp(growth * t)
    points = np.column_stack((300 + r * np.cos(t), 300 + (-1 if mirrored else 1) * r * np.sin(t)))
    ImageDraw.Draw(image).line([tuple(p) for p in points], fill='black', width=4)
    return image


class GeometryTests(SimpleTestCase):
    def test_r3_textured_crossing_spiral(self):
        rng = np.random.default_rng(23)
        image = Image.fromarray(rng.normal(180, 15, (600, 600, 3)).clip(0, 255).astype('uint8'))
        t = np.linspace(0, 3 * math.pi, 1200)
        r = 12 * np.exp(GROWTH * t)
        points = np.column_stack((300 + r * np.cos(t), 300 + r * np.sin(t)))
        draw = ImageDraw.Draw(image)
        draw.line([tuple(p) for p in points], fill=(35, 40, 30), width=5)
        draw.line((50, 350, 550, 350), fill=(100, 100, 100), width=2)
        found = [c for c in analyze(image) if c.kind == 'spiral']
        self.assertEqual(len(found), 1)
        self.assertLess(abs(found[0].growth - PHI), .08)
        self.assertGreaterEqual(found[0].support, 72)

    def test_r3_full_pipeline_negative_patterns(self):
        for kind in ('circle', 'archimedean', 'nongolden', 'grid'):
            with self.subTest(kind=kind):
                image = Image.new('RGB', (600, 600), 'white')
                draw = ImageDraw.Draw(image)
                if kind == 'circle':
                    draw.ellipse((90, 90, 510, 510), outline='black', width=5)
                elif kind == 'grid':
                    for value in range(40, 600, 40):
                        draw.line((value, 0, value, 600), fill='black', width=3)
                        draw.line((0, value, 600, value), fill='black', width=3)
                else:
                    t = np.linspace(0, 4 * math.pi, 1200)
                    r = 12 * np.exp(.18 * t) if kind == 'nongolden' else 12 + 15 * t
                    points = np.column_stack((300 + r * np.cos(t), 300 + r * np.sin(t)))
                    draw.line([tuple(p) for p in points], fill='black', width=5)
                self.assertEqual([c for c in analyze(image) if c.kind == 'spiral'], [])

    def test_r3_photographic_controls(self):
        from skimage import data
        for name in ('camera', 'coffee', 'astronaut', 'chelsea'):
            with self.subTest(name=name):
                image = Image.fromarray(getattr(data, name)()).convert('RGB')
                self.assertEqual([c for c in analyze(image) if c.kind == 'spiral'], [])

    def test_r3_photo_background_composite(self):
        from skimage import data
        image = Image.fromarray(data.coffee()).resize((700, 700))
        t = np.linspace(0, 3 * math.pi, 1400)
        r = 12 * np.exp(GROWTH * t)
        points = np.column_stack((350 + r * np.cos(t), 350 + r * np.sin(t)))
        ImageDraw.Draw(image).line([tuple(p) for p in points], fill='white', width=6)
        found = [c for c in analyze(image) if c.kind == 'spiral']
        self.assertEqual(len(found), 1)
        self.assertGreaterEqual(found[0].support, 72)

    def test_r2_golden_frame_and_negative_square(self):
        self.assertEqual(len(analyze(Image.new('RGB', (809, 500), 'white'))), 1)
        self.assertEqual(analyze(Image.new('RGB', (500, 500), 'white')), [])

    def test_r2_rectangle_duplicate_suppression(self):
        image = Image.new('RGB', (700, 700), 'white')
        ImageDraw.Draw(image).rectangle((100, 100, 504, 350), outline='black', width=4)
        found = analyze(image)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].kind, 'rectangle')

    def test_r2_non_golden_rectangle(self):
        image = Image.new('RGB', (700, 700), 'white')
        ImageDraw.Draw(image).rectangle((100, 100, 500, 300), outline='black', width=4)
        self.assertEqual(analyze(image), [])

    def test_r3_spiral_fit_both_handednesses(self):
        for sign in (-1, 1):
            t = np.linspace(0, 3 * math.pi, 400)
            r = 12 * np.exp(GROWTH * t)
            points = np.column_stack((300 + r * np.cos(t), 300 + sign * r * np.sin(t)))
            candidate = fit_spiral(points)
            self.assertIsNotNone(candidate)
            self.assertLess(candidate.error, 0.1)

    def test_r3_end_to_end_spiral(self):
        for mirrored in (False, True):
            found = analyze(spiral_image(mirrored=mirrored))
            self.assertEqual(len([c for c in found if c.kind == 'spiral']), 1)

    def test_r3_circle_and_wrong_growth_rejected(self):
        t = np.linspace(0, 2 * math.pi, 400)
        self.assertIsNone(fit_spiral(np.column_stack((100 * np.cos(t), 100 * np.sin(t)))))
        r = 10 * np.exp(0.15 * t)
        self.assertIsNone(fit_spiral(np.column_stack((r * np.cos(t), r * np.sin(t)))))


class UploadTests(SimpleTestCase):
    def test_r1_valid_normalized_image(self):
        result = decode(upload(Image.new('RGB', (100, 100), 'white')))
        self.assertEqual(result.size, (100, 100))
        self.assertEqual(result.info, {})

    def test_r1_bad_file_and_size(self):
        with self.assertRaises(ValueError):
            decode(SimpleUploadedFile('x.png', b'not an image'))
        item = upload(Image.new('RGB', (100, 100)))
        item.size = 11 * 1024 * 1024
        with self.assertRaisesRegex(ValueError, 'size'):
            decode(item)

    def test_r1_pixel_limit(self):
        with self.assertRaisesRegex(ValueError, 'pixels'):
            decode(upload(Image.new('RGB', (20, 20))))


class FlowTests(SimpleTestCase):
    def setUp(self):
        from .limits import limiter
        limiter.clear()
    @override_settings(DEBUG=True, ALLOWED_HOSTS=['localhost', 'testserver', 'example.com'])
    def test_preview_null_origin_requires_tokens_and_loopback(self):
        client = Client(enforce_csrf_checks=True, HTTP_HOST='localhost')
        self.assertContains(client.get('/'), 'Golden Ratio Tester')
        token = client.cookies['csrftoken'].value
        headers = {'HTTP_ORIGIN': 'null', 'REMOTE_ADDR': '127.0.0.1'}
        self.assertEqual(client.post('/language/', {'language': 'en'}, **headers).status_code, 403)
        self.assertEqual(client.post('/language/', {'language': 'en', 'csrfmiddlewaretoken': 'a' * 64}, **headers).status_code, 403)
        data = {'language': 'en', 'csrfmiddlewaretoken': token}
        self.assertEqual(client.post('/language/', data, **headers).status_code, 302)
        for remote, host in [('192.0.2.1', 'localhost'), ('127.0.0.1', 'example.com')]:
            self.assertEqual(client.post('/language/', data, HTTP_ORIGIN='null', REMOTE_ADDR=remote,
                                         HTTP_HOST=host).status_code, 403)
        self.assertEqual(client.post('/language/', data, secure=True, **headers).status_code, 403)
        with self.settings(DEBUG=False):
            self.assertEqual(client.post('/language/', data, **headers).status_code, 403)
        result = client.post('/', {'image': upload(Image.new('RGB', (809, 500), 'white')),
                                   'csrfmiddlewaretoken': token}, **headers)
        self.assertEqual(result.status_code, 302)
        result_token = result.url.split('/')[2]
        download = client.get(f'/image/{result_token}/download/')
        self.assertIn('golden-ratio-tester.png', download['Content-Disposition'])
        self.assertEqual(client.post(f'/delete/{result_token}/', {'csrfmiddlewaretoken': token}, **headers).status_code, 302)

    def test_https_without_origin_uses_same_origin_referer(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get('/', secure=True)
        self.assertEqual(response['Referrer-Policy'], 'same-origin')
        token = client.cookies['csrftoken'].value
        data = {'language': 'en', 'csrfmiddlewaretoken': token}
        self.assertEqual(client.post('/language/', data, secure=True,
                                    HTTP_REFERER='https://testserver/').status_code, 302)
        self.assertEqual(client.post('/language/', data, secure=True,
                                    HTTP_REFERER='https://untrusted.example/').status_code, 403)

    def test_r4_r5_r6_complete_flow(self):
        response = self.client.get('/')
        self.assertContains(response, 'lang="es"')
        self.assertNotIn('golden_ratio_tester_language', response.cookies)
        response = self.client.post('/language/', {'language': 'en'})
        self.assertEqual(response.cookies['golden_ratio_tester_language']['max-age'], 180 * 86400)
        response = self.client.post('/', {'image': upload(Image.new('RGB', (809, 500), 'white'))})
        self.assertEqual(response.status_code, 302)
        url = response.url
        token = url.split('/')[2]
        result = self.client.get(url)
        self.assertContains(result, 'compatible candidates')
        self.assertContains(result, 'https://en.wikipedia.org/wiki/Golden_ratio')
        self.assertContains(self.client.get(url + '?guides=0'), '/original/')
        data = self.client.get(f'/image/{token}/download/')
        self.assertIn('attachment', data['Content-Disposition'])
        self.assertEqual(Image.open(BytesIO(data.content)).size, (809, 500))
        self.assertEqual(self.client.get('/image/unknown/original/').status_code, 404)
        self.assertEqual(self.client.get(f'/delete/{token}/').status_code, 405)
        self.client.post(f'/delete/{token}/')
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post('/language/', {'language': 'reset'}).cookies['golden_ratio_tester_language']['max-age'], 0)

    def test_r6_csrf_and_headers(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/language/', {'language': 'en'}).status_code, 403)
        response = client.get('/')
        self.assertIn("script-src 'self'", response['Content-Security-Policy'])
        self.assertNotIn("unsafe-inline", response['Content-Security-Policy'])
        self.assertIn('no-store', response['Cache-Control'])
        token = client.cookies['csrftoken'].value
        valid = client.post('/language/', {'language': 'en', 'csrfmiddlewaretoken': token},
                            HTTP_ORIGIN='http://testserver')
        self.assertEqual(valid.status_code, 302)
        invalid = client.post('/language/', {'language': 'es', 'csrfmiddlewaretoken': token},
                              HTTP_ORIGIN='https://untrusted.example')
        self.assertEqual(invalid.status_code, 403)

    def test_r5_translation_parity(self):
        self.assertEqual(set(COPY['es']), set(COPY['en']))
        self.assertContains(self.client.get('/'), 'Ctrl+V o ⌘V')
        self.client.post('/language/', {'language': 'en'})
        response = self.client.get('/')
        self.assertContains(response, 'Ctrl+V or ⌘V')
        self.assertContains(response, '/static/lab/app.js')

    def test_r6_expiry_and_memory_bound(self):
        store = ResultStore(ttl=0.04, max_bytes=8)
        token = store.put({'original': b'abcd', 'overlay': b'efgh'})
        second = store.put({'original': b'abcd', 'overlay': b'efgh'})
        self.assertIsNone(store.get(token))
        time.sleep(0.08)
        self.assertEqual(store.used, 0)
        self.assertIsNone(store.get(second))
