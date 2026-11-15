from urllib.parse import urlsplit

from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware


class LocalPreviewCsrfMiddleware(CsrfViewMiddleware):
    """Token validation stays in Django; only local debug previews get an origin exception."""

    def _origin_verified(self, request):
        if request.META.get('HTTP_ORIGIN') == 'null' and settings.DEBUG and not request.is_secure():
            host = urlsplit('http://' + request.get_host()).hostname
            if (host in ('localhost', '127.0.0.1', '::1')
                    and request.META.get('REMOTE_ADDR') in ('127.0.0.1', '::1')):
                return True
        return super()._origin_verified(request)
