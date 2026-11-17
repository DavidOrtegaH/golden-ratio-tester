"""Build self-contained static Pages assets. No image data or credentials used."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import argparse
import json
import os
import re
import shutil
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'golden_ratio_tester.settings')
os.environ.setdefault('DJANGO_DEBUG', '1')
VERSION = '314.0.8'
BASE = f'https://cdn.jsdelivr.net/pyodide/v{VERSION}/full/'
CACHE = ROOT / 'artifacts' / f'pyodide-{VERSION}'
DIST = ROOT / 'artifacts' / 'pages'
LOCK = ROOT / 'pages' / 'runtime-lock.json'
PROFILE = json.loads((ROOT / 'pages' / 'package-profile.json').read_text())


def download(name, expected=None):
    if '/' in name or '\\' in name or name.startswith('.'):
        raise ValueError('Unexpected runtime filename')
    target = CACHE / name
    if not target.exists() or (expected and sha256(target.read_bytes()).hexdigest() != expected):
        with urllib.request.urlopen(BASE + name, timeout=120) as response:
            content = response.read()
        if expected and sha256(content).hexdigest() != expected:
            raise ValueError(f'Runtime integrity mismatch: {name}')
        target.write_bytes(content)
    return sha256(target.read_bytes()).hexdigest()


def prepare_lock():
    download('pyodide-lock.json')
    upstream = json.loads((CACHE / 'pyodide-lock.json').read_text())
    packages = upstream['packages']
    names = set()

    def collect(name):
        name = name.lower().replace('_', '-')
        if name in names:
            return
        names.add(name)
        for dep in PROFILE['dependency_overrides'].get(name, packages[name]['depends']):
            collect(dep)

    for name in PROFILE['roots']:
        collect(name)
    files = {packages[name]['file_name']: packages[name]['sha256'] for name in sorted(names)}
    for name in ['pyodide.mjs', 'pyodide.asm.mjs', 'pyodide.asm.wasm', 'python_stdlib.zip', 'pyodide-lock.json']:
        files[name] = download(name)
    LOCK.write_text(json.dumps({'version': VERSION, 'source': BASE, 'profile': PROFILE, 'packages': {
        name: packages[name]['version'] for name in sorted(names)}, 'files': files}, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lock-runtime', action='store_true', help='Explicitly refresh pinned runtime hashes')
    options = parser.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    if options.lock_runtime:
        prepare_lock()
    lock = json.loads(LOCK.read_text())
    if lock['version'] != VERSION or lock['source'] != BASE or lock['profile'] != PROFILE:
        raise ValueError('Runtime manifest does not match the pinned release')
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda item: download(*item), lock['files'].items()))
    # Only replace the named build directory inside the repository's artifacts.
    if DIST.exists():
        if DIST.resolve().parent != (ROOT / 'artifacts').resolve():
            raise ValueError('Unexpected output path')
        shutil.rmtree(DIST)
    (DIST / 'runtime').mkdir(parents=True)
    for name in lock['files']:
        shutil.copy2(CACHE / name, DIST / 'runtime' / name)
    # Application-specific lock profile: the exact upstream wheels are untouched.
    # We use only morphology, never skimage's codecs, plotting or graph modules.
    runtime_lock = json.loads((CACHE / 'pyodide-lock.json').read_text())
    runtime_lock['packages'] = {name: value for name, value in runtime_lock['packages'].items() if name in lock['packages']}
    for name, deps in PROFILE['dependency_overrides'].items():
        runtime_lock['packages'][name]['depends'] = deps
    runtime_lock_path = DIST / 'runtime' / 'pyodide-lock.json'
    runtime_lock_path.write_text(json.dumps(runtime_lock), encoding='utf-8')
    lock['served_lock_sha256'] = sha256(runtime_lock_path.read_bytes()).hexdigest()
    import django
    django.setup()
    from django.template.loader import render_to_string
    from lab.copy import COPY
    copy = deepcopy(COPY)
    overrides = {
        'es': {
            'paste_hint': 'También puedes copiar una imagen y pegarla aquí con Ctrl+V o ⌘V. Se analizará en tu dispositivo cuando pulses Analizar.',
            'method_intro': 'Una coincidencia visual merece una comprobación: buscamos relaciones que se puedan medir.',
            'privacy_body': 'En esta versión de GitHub Pages, el cálculo se realiza en el navegador. La selección y el resultado permanecen en memoria hasta que los eliminas, eliges otra imagen o cierras la página; el resultado caduca a los 15 minutos. GitHub sirve la página y los archivos del motor y recibe los datos habituales de conexión.',
            'privacy_rate': 'El primer análisis descarga un motor de cálculo de aproximadamente 50 MB. Puede tardar más en móviles y conexiones lentas. Puedes cancelar el análisis.',
            'cookies': 'Solo guardamos golden_ratio_tester_language después de que elijas un idioma: dura 180 días y se puede borrar aquí. No usamos cookies de publicidad, analítica ni seguimiento. GitHub puede conservar registros técnicos del alojamiento según su política de privacidad.',
            'expiry': 'El resultado se borra de esta página a los 15 minutos. La descarga siempre incluye las guías, aunque estén ocultas.',
            'loading_runtime': 'Preparando el motor local… La primera vez puede tardar y descargar unos 50 MB.',
            'runtime_error': 'No se pudo ejecutar el motor local. Comprueba la conexión y prueba de nuevo; si persiste, usa un navegador actualizado o una imagen más pequeña.',
            'timeout': 'El análisis ha superado los tres minutos. Prueba una imagen más pequeña o sencilla.',
            'cancel': 'Cancelar análisis', 'cancelled': 'Análisis cancelado. Puedes volver a intentarlo.',
            'no_script': 'Esta versión necesita JavaScript y WebAssembly. Activa JavaScript o ejecuta la versión Django del repositorio.',
        },
        'en': {
            'paste_hint': 'You can also copy an image and paste it here with Ctrl+V or ⌘V. It is analyzed on your device when you press Analyze.',
            'method_intro': 'A visual coincidence deserves a check: we look for relationships that can be measured.',
            'privacy_body': 'In this GitHub Pages version, calculations run in the browser. The selection and result stay in memory until you delete them, choose another image, or close the page; the result expires after 15 minutes. GitHub serves the page and engine files and receives normal connection data.',
            'privacy_rate': 'The first analysis downloads a calculation engine of approximately 50 MB. Mobile devices and slow connections may take longer. You can cancel analysis.',
            'cookies': 'We only store golden_ratio_tester_language after you choose a language: it lasts 180 days and can be deleted here. We use no advertising, analytics, or tracking cookies. GitHub may retain technical hosting logs under its privacy policy.',
            'expiry': 'The result is cleared from this page after 15 minutes. Downloads always include the guides, even when hidden.',
            'loading_runtime': 'Preparing the local engine… The first analysis may take longer and download around 50 MB.',
            'runtime_error': 'Could not run the local engine. Check your connection and try again; if it persists, use an updated browser or a smaller image.',
            'timeout': 'Analysis exceeded three minutes. Try a smaller or simpler image.',
            'cancel': 'Cancel analysis', 'cancelled': 'Analysis cancelled. You can try again.',
            'no_script': 'This version requires JavaScript and WebAssembly. Enable JavaScript or run the Django version from the repository.',
        },
    }
    total_mb = sum((CACHE / name).stat().st_size for name in lock['files']) / 1024**2
    for lang in copy:
        copy[lang].update(overrides[lang])
        for key in ('privacy_rate', 'loading_runtime'):
            copy[lang][key] = copy[lang][key].replace('50', str(round(total_mb)))
    (DIST / 'copy.json').write_text(json.dumps(copy, ensure_ascii=False), encoding='utf-8')
    html = render_to_string('lab/index.html', {'lang': 'es', 't': copy['es'], 'csrf_token': 'NOTPROVIDED'})
    html = re.sub(r'<input[^>]+name="csrfmiddlewaretoken"[^>]*>', '', html)
    html = html.replace('action="/language/"', 'action="./"').replace('action="/"', 'action="./"')
    html = html.replace('href="/#method"', 'href="#method"').replace('href="/"', 'href="./"')
    html = html.replace('/static/lab/', './assets/').replace('./assets/app.js', './app.js')
    # Prevent accidental form navigation before Stimulus starts (or when unavailable).
    html = html.replace('data-busy-control', 'data-busy-control disabled data-start-disabled')
    html = html.replace('</form></div></div>', '<button type="button" class="btn btn-outline-danger mt-2" hidden data-cancel data-action="workspace#cancel" data-i18n="cancel">Cancelar análisis</button></form></div></div>')
    html = html.replace('<div id="analysis-result"', f'<noscript><p class="alert alert-warning">{copy["es"]["no_script"]} / {copy["en"]["no_script"]}</p></noscript><div id="analysis-result"')
    csp = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self' blob:; connect-src 'self'; worker-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'"
    html = html.replace('<meta charset="utf-8">', f'<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="{csp}"><meta name="referrer" content="strict-origin-when-cross-origin">')
    html = html.replace('</body>', (ROOT / 'pages' / 'results.html').read_text(encoding='utf-8') + '</body>')
    (DIST / 'index.html').write_text(html, encoding='utf-8')
    (DIST / '.nojekyll').touch()
    shutil.copytree(ROOT / 'lab' / 'static' / 'lab', DIST / 'assets')
    with zipfile.ZipFile(DIST / 'detector.zip', 'w', zipfile.ZIP_DEFLATED) as output:
        for name in ['__init__.py', 'geometry.py', 'contours.py', 'templatesearch.py']:
            output.write(ROOT / 'lab' / name, f'lab/{name}')
    shutil.copy2(ROOT / 'LICENSE', DIST / 'LICENSE.txt')
    notices = ['Third-party runtime components for Golden Ratio Tester',
               f'Pyodide {VERSION}: https://github.com/pyodide/pyodide (MPL-2.0)',
               'CPython: https://docs.python.org/3/license.html',
               'Unmodified distribution wheels; upstream license notices follow.']
    for name in lock['files']:
        if not name.endswith('.whl'):
            continue
        with zipfile.ZipFile(CACHE / name) as wheel:
            for member in wheel.namelist():
                leaf = member.rsplit('/', 1)[-1].lower()
                if '.dist-info/' in member and ('license' in leaf or 'copying' in leaf or 'notice' in leaf):
                    notices.extend(['\n' + name + ' / ' + member, wheel.read(member).decode('utf-8', errors='replace')])
    (DIST / 'THIRD_PARTY_NOTICES.txt').write_text('\n'.join(notices), encoding='utf-8')
    (DIST / 'runtime-manifest.json').write_text(json.dumps(lock, indent=2) + '\n')
    print(f'Pages prepared at {DIST}; runtime {total_mb:.1f} MiB (pinned and verified).')


if __name__ == '__main__':
    main()
