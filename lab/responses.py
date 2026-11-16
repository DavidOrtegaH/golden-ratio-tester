from django.http import JsonResponse
from django.shortcuts import render
from .copy import COPY

LANGUAGE_COOKIE = 'golden_ratio_tester_language'
LEGACY_LANGUAGE_COOKIE = 'aurea_language'  # Read only, until the next explicit choice.


def context(request, **extra):
    language = request.COOKIES.get(LANGUAGE_COOKIE, request.COOKIES.get(LEGACY_LANGUAGE_COOKIE, 'es'))
    language = language if language in COPY else 'es'
    return {'lang': language, 't': COPY[language], **extra}


def wants_json(request):
    return 'application/json' in request.headers.get('Accept', '')


def failure(request, code, status):
    ctx = context(request)
    message = ctx['t'][code]
    if wants_json(request):
        return JsonResponse({'ok': False, 'code': code, 'message': message}, status=status)
    return render(request, 'lab/error.html', {**ctx, 'error': message}, status=status)


def csrf_failure(request, reason=''):
    return failure(request, 'csrf', 403)


def bad_request(request, exception):
    return failure(request, 'request_error', 400)


def not_found(request, exception):
    return failure(request, 'expired', 404)


def server_error(request):
    return failure(request, 'server_error', 500)
