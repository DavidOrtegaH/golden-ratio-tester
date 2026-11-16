from urllib.parse import urlsplit
from django.conf import settings
from django.core.exceptions import RequestDataTooBig, TooManyFilesSent, TooManyFieldsSent


class PreviewRequestMiddleware:
    """Bound form parsing and normalize only the explicitly allowed local preview.

    Django's unmodified CsrfViewMiddleware still checks every token and origin.
    Production never normalizes opaque origins.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        from .responses import failure
        if request.method == 'POST':
            try:
                request.POST  # Parse once with bounded handlers before CSRF examines it.
            except RequestDataTooBig:
                return failure(request, 'size', 413)
            except (TooManyFilesSent, TooManyFieldsSent):
                return failure(request, 'request_error', 400)
        if request.META.get('HTTP_ORIGIN') == 'null' and settings.DEBUG and not request.is_secure():
            host = urlsplit('http://' + request.get_host()).hostname
            if (host in ('localhost', '127.0.0.1', '::1')
                    and request.META.get('REMOTE_ADDR') in ('127.0.0.1', '::1')):
                request.META['HTTP_ORIGIN'] = 'http://' + request.get_host()
