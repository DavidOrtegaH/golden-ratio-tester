class PrivacyHeaders:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['Cache-Control'] = 'no-store, private'
        response['X-Robots-Tag'] = 'noindex, nofollow'
        response['Content-Security-Policy'] = "default-src 'self'; connect-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response


class RequestLimits:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from .responses import failure
        from .uploads import MAX_BODY_BYTES
        try:
            length = int(request.META.get('CONTENT_LENGTH') or 0)
        except ValueError:
            return failure(request, 'request_error', 400)
        if length < 0:
            return failure(request, 'request_error', 400)
        if length > MAX_BODY_BYTES:
            return failure(request, 'size', 413)
        return self.get_response(request)

    def process_exception(self, request, exception):
        from django.core.exceptions import RequestDataTooBig, TooManyFilesSent, TooManyFieldsSent
        from .responses import failure
        if isinstance(exception, RequestDataTooBig):
            return failure(request, 'size', 413)
        if isinstance(exception, (TooManyFilesSent, TooManyFieldsSent)):
            return failure(request, 'request_error', 400)
