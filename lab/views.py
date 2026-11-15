import threading
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .copy import COPY
from .geometry import analyze
from .imaging import decode, overlay, png
from .store import store

analysis_slot = threading.BoundedSemaphore(1)


def context(request, **extra):
    language = request.COOKIES.get('aurea_language', 'es')
    language = language if language in COPY else 'es'
    return {'lang': language, 't': COPY[language], **extra}


@require_http_methods(['GET', 'POST'])
def index(request):
    error = None
    status = 200
    if request.method == 'POST':
        upload = request.FILES.get('image')
        if upload is None:
            error, status = 'missing', 400
        elif not analysis_slot.acquire(blocking=False):
            error, status = 'busy', 503
        else:
            try:
                source = decode(upload)
                candidates = analyze(source)
                token = store.put({'original': png(source), 'overlay': png(overlay(source, candidates)),
                                   'candidates': candidates, 'size': source.size})
                return redirect('result', token=token)
            except ValueError as exc:
                error = str(exc) if str(exc) in COPY['es'] else 'format'
                status = 400
            finally:
                analysis_slot.release()
    ctx = context(request)
    ctx['error'] = ctx['t'].get(error)
    return render(request, 'lab/index.html', ctx, status=status)


@require_POST
def language(request):
    choice = request.POST.get('language')
    token = request.POST.get('token', '')
    response = redirect('result', token=token) if store.get(token) else redirect('home')
    if choice in COPY:
        response.set_cookie('aurea_language', choice, max_age=180 * 86400,
                            httponly=True, secure=not settings.DEBUG, samesite='Lax')
    elif choice == 'reset':
        response.delete_cookie('aurea_language', samesite='Lax')
    return response


@require_GET
def result(request, token):
    value = store.get(token)
    ctx = context(request, token=token)
    if value is None:
        ctx['error'] = ctx['t']['expired']
        return render(request, 'lab/index.html', ctx, status=404)
    visible = request.GET.get('guides') != '0'
    rows = [{'number': i, 'label': ctx['t'][c.kind], 'error': f'{c.error:.2f}%',
             'ratio': '—' if c.kind == 'spiral' else f'{c.ratio:.4f}'}
            for i, c in enumerate(value['candidates'], 1)]
    ctx.update(rows=rows, count=len(rows), visible=visible, size=value['size'])
    return render(request, 'lab/result.html', ctx)


@require_GET
def image(request, token, variant):
    value = store.get(token)
    if value is None or variant not in ('original', 'overlay', 'download'):
        return HttpResponseNotFound(context(request)['t']['expired'])
    response = HttpResponse(value['original' if variant == 'original' else 'overlay'], content_type='image/png')
    if variant == 'download':
        response['Content-Disposition'] = 'attachment; filename="golden-ratio-tester.png"'
    return response


@require_POST
def delete(request, token):
    store.delete(token)
    return redirect('home')
