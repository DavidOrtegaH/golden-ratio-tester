import logging
import threading
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .copy import COPY
from .geometry import analyze
from .imaging import decode, overlay, png
from .limits import limiter
from .responses import context, failure, wants_json, LANGUAGE_COOKIE, LEGACY_LANGUAGE_COOKIE
from .store import store

analysis_slot = threading.BoundedSemaphore(1)
logger = logging.getLogger('django.request')


def result_context(request, token, value, visible=True):
    ctx = context(request, token=token, expires_in=store.remaining(token))
    rows = [{'number': i, 'label': ctx['t'][c.kind], 'error': f'{c.error:.2f}%',
             'ratio': '—' if c.kind == 'spiral' else f'{c.ratio:.4f}',
             'growth': f'{c.growth:.4f}' if c.growth is not None else '—',
             'support': f'{c.support:.0f}%' if c.support is not None else '—',
             'metric': ctx['t'][c.metric if c.kind == 'spiral' else 'aspect_error']}
            for i, c in enumerate(value['candidates'], 1)]
    ctx.update(rows=rows, count=len(rows), visible=visible, size=value['size'])
    return ctx


def payload(request, token='', value=None):
    ctx = context(request)
    html = render_to_string('lab/_results.html', result_context(request, token, value), request=request) if value else ''
    return {'ok': True, 'lang': ctx['lang'], 'copy': ctx['t'], 'token': token if value else '',
            'html': html, 'expires_in': store.remaining(token) if value else 0}


@require_http_methods(['GET', 'POST'])
def index(request):
    if request.method == 'GET':
        return render(request, 'lab/index.html', context(request))
    upload = request.FILES.get('image')
    if upload is None:
        return failure(request, 'missing', 400)
    if not limiter.allow(request.META.get('REMOTE_ADDR', ''), settings.ANALYSIS_RATE_LIMIT):
        response = failure(request, 'rate_limit', 429)
        response['Retry-After'] = '60'
        return response
    if not analysis_slot.acquire(blocking=False):
        response = failure(request, 'busy', 503)
        response['Retry-After'] = '5'
        return response
    source = None
    annotated = None
    try:
        source = decode(upload)
        candidates = analyze(source)
        annotated = overlay(source, candidates)
        value = {'original': png(source), 'overlay': png(annotated),
                 'candidates': candidates, 'size': source.size}
        token = store.put(value)
        if wants_json(request):
            return JsonResponse(payload(request, token, value))
        return redirect('result', token=token)
    except ValueError as exc:
        code = str(exc) if str(exc) in ('size', 'pixels', 'format') else 'format'
        return failure(request, code, 413 if code == 'size' else 400)
    except Exception as exc:
        logger.error('Image analysis failed (%s)', type(exc).__name__)
        return failure(request, 'server_error', 500)
    finally:
        if source is not None:
            source.close()
        if annotated is not None:
            annotated.close()
        analysis_slot.release()


@require_POST
def language(request):
    choice = request.POST.get('language')
    if choice not in (*COPY.keys(), 'reset'):
        return failure(request, 'request_error', 400)
    selected = choice if choice in COPY else 'es'
    token = request.POST.get('token', '')
    value = store.get(token)
    request.COOKIES[LANGUAGE_COOKIE] = selected
    if wants_json(request):
        response = JsonResponse(payload(request, token, value))
    else:
        response = redirect('result', token=token) if value else redirect('home')
    if choice in COPY:
        response.set_cookie(LANGUAGE_COOKIE, choice, max_age=180 * 86400,
                            httponly=True, secure=not settings.DEBUG, samesite='Lax')
    else:
        response.delete_cookie(LANGUAGE_COOKIE, samesite='Lax')
    if LEGACY_LANGUAGE_COOKIE in request.COOKIES:
        response.delete_cookie(LEGACY_LANGUAGE_COOKIE, samesite='Lax')
    return response


@require_GET
def result(request, token):
    value = store.get(token)
    if value is None:
        return failure(request, 'expired', 404)
    if wants_json(request):
        return JsonResponse(payload(request, token, value))
    return render(request, 'lab/index.html', result_context(request, token, value, request.GET.get('guides') != '0'))


@require_GET
def image(request, token, variant):
    value = store.get(token)
    if value is None or variant not in ('original', 'overlay', 'download'):
        return failure(request, 'expired', 404)
    response = HttpResponse(value['original' if variant == 'original' else 'overlay'], content_type='image/png')
    if variant == 'download':
        response['Content-Disposition'] = 'attachment; filename="golden-ratio-tester.png"'
    return response


@require_POST
def delete(request, token):
    store.delete(token)
    return JsonResponse({'ok': True}) if wants_json(request) else redirect('home')
