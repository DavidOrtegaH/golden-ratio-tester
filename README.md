# Áurea Lab

**Geometría, no casualidad.** Una aplicación web en español e inglés para buscar
geometrías compatibles con la proporción áurea en imágenes, revisar sus medidas
y descargar las anotaciones. Inspirada por los debates sobre el Spin de
*JoJo’s Bizarre Adventure: Steel Ball Run*. Proyecto independiente, sin afiliación.

Autor original: **David ([@DavidOrtegaH](https://github.com/DavidOrtegaH))**.
Código abierto bajo [MIT](LICENSE). Deben conservarse el aviso de copyright y la
licencia en las copias o partes sustanciales del software.

## Qué hace

- Sube JPG, PNG o WebP estático de hasta 10 MiB y 20 megapíxeles.
- Cuenta encuadres, contornos rectangulares y trazos espirales que cumplen los
  criterios definidos; muestra tipo, proporción y error.
- Superpone rectángulos con divisiones de referencia o el arco de espiral ajustado.
- Permite mostrar/ocultar las guías y descargar un PNG anotado a la resolución original
  normalizada por orientación EXIF. La descarga no incluye metadatos del original.
- Selector Español/English con banderas, Wikipedia por idioma y cookie de preferencia.
- Interfaz responsive con formularios estándar, sin JavaScript de aplicación.
- Elimina imágenes al pulsar el botón o al expirar el plazo de 15 minutos.

## Qué NO demuestra

El número es un **recuento de candidatos bajo criterios concretos**, no un número
universal de todas las relaciones áureas de una fotografía. La versión inicial
no reconoce objetos semánticamente ni decide si una composición artística es áurea.

Un rectángulo admite hasta un 3% de desviación respecto a φ y debe tener ángulos
aproximadamente rectos. No se inventan recortes arbitrarios. Las dos caras del
borde de un mismo rectángulo se deduplican por solapamiento.

Las espirales se buscan en trazos aislados segmentados por umbral de Otsu, se
reducen a un esqueleto y se ajustan a `r = a·exp(b·θ)`, con
`|b| = 2·ln(φ)/π`. Se exige un recorrido de al menos π radianes, radio máximo/mínimo
de al menos 2 y error RMS radial ≤2,5% de la diagonal del trazo. El error de espiral
y el error de relación rectangular son métricas diferentes, no probabilidades.

El análisis usa una imagen de hasta 1200 píxeles en su lado mayor. Considera como
máximo 300 contornos rectangulares y 24 componentes para espirales; puede omitir
elementos pequeños o escenas muy densas. Texturas, perspectiva, cruces, guías
superpuestas y oclusiones pueden impedir la detección. No se afirma que un
rectángulo implique una espiral, ni que cero candidatos demuestre ausencia.
Las aproximaciones de Fibonacci con arcos de circunferencia tampoco son exactamente
la espiral logarítmica áurea.

## Stack

Python 3.12+, Django 5.2 LTS, OpenCV, NumPy, SciPy, scikit-image y Pillow.
Interfaz con plantillas Django, Bootstrap 5 y Sass. No requiere base de datos.
Las dependencias exactas probadas están en `requirements.lock` y `package-lock.json`.
Waitress está disponible para un servidor WSGI de un único proceso.

## Arranque local (PowerShell)

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock
npm.cmd ci
npm.cmd run build
.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

Abre http://127.0.0.1:8000 en un navegador normal. No hay migraciones ni cuentas.
El CSS compilado está versionado; Node solo es necesario para modificar Sass.
En Linux/macOS sustituye `.venv/Scripts/python.exe` por `.venv/bin/python` y `npm.cmd` por `npm`.

## SpecDD y comprobación

La especificación se escribió y confirmó antes de la implementación:
[`specs/001-golden-analysis.md`](specs/001-golden-analysis.md).

```powershell
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py test -v 2
npm.cmd run build
```

Las 13 pruebas cubren positivos y negativos sintéticos, ambos sentidos de giro,
deduplicación, subida inválida, idiomas, CSRF, descarga, eliminación y caducidad.
No equivalen a una evaluación estadística del detector sobre fotografías reales.
CI repite las pruebas y comprueba que el Sass compilado no tenga cambios pendientes.

Ramas: `feature` → `develop` → `release` → `main`. Conventional Commits en inglés.
Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

### Compatibilidad

Diseñado para versiones actuales de Chrome, Edge, Firefox y Safari, incluyendo
navegadores móviles. No depende de JavaScript ni de APIs experimentales.
Se han comprobado anchuras de 390 y 768 píxeles en el navegador integrado sin
desbordamiento horizontal. **La matriz de navegadores externos y dispositivos
físicos todavía no está verificada.** El navegador integrado usado para QA envió
`Origin: null` al enviar formularios y Django lo rechazó correctamente; usa un
navegador normal. No se ha relajado CSRF para acomodar esa limitación.

## Privacidad y cookies

Las imágenes se envían al servidor local que ejecuta la aplicación, se decodifican
y se mantienen solo en memoria. No se envían a proveedores de IA ni se usan para
entrenamiento. El almacén admite hasta 192 MiB de PNGs normalizados y anotados;
los resultados antiguos pueden expulsarse antes de 15 minutos. Se usa un token
aleatorio de acceso: quien tenga la URL puede ver ese resultado mientras exista.
Las respuestas incluyen `no-store`, `no-referrer`, CSP y exclusión de indexación.

| Cookie propia | Finalidad | Duración |
| --- | --- | --- |
| `csrftoken` | Proteger los formularios | Sesión del navegador |
| `aurea_language` | Recordar una elección explícita de idioma | 180 días |

No hay analítica, publicidad, recursos de terceros ni consentimiento preseleccionado.
La preferencia se borra desde «Privacidad y cookies». Este uso exclusivamente
funcional de un idioma elegido por el usuario sigue el criterio de la
[guía AEPD](https://www.aepd.es/guias/guia-cookies.pdf). El responsable de una futura
instancia pública debe completar su identificación, contacto y política de privacidad
según su alojamiento y tratamiento real; este repositorio no certifica cumplimiento legal.

## Antes de alojarla públicamente

Esta entrega es una aplicación local y código fuente; no incluye hosting público.
El backend Python no puede publicarse como sitio estático en GitHub Pages ni como
un Worker JavaScript sin cambiar la arquitectura.

1. Configura `DJANGO_DEBUG=0`, un `DJANGO_SECRET_KEY` aleatorio y
   `DJANGO_ALLOWED_HOSTS` con los dominios exactos (ver `.env.example`; no se carga
   automáticamente: establece estas variables en el entorno del servicio).
2. Ejecuta `manage.py collectstatic --noinput`; sirve `staticfiles/` desde el proxy.
3. Usa un proxy HTTPS con límite de cuerpo de 11 MiB, límite de peticiones y
   tiempos de espera. No registres cuerpos, nombres originales ni URLs completas
   de resultados. Restringe el backend a loopback.
4. Inicia **un único proceso** Waitress detrás del proxy TLS:
   `.venv/Scripts/waitress-serve.exe --listen=127.0.0.1:8000 --threads=4 --url-scheme=https aurea.wsgi:application`.
   `--url-scheme=https` solo es correcto detrás del proxy HTTPS indicado.
5. Ejecuta `manage.py check --deploy` con el entorno de producción y completa
   las pruebas en navegadores reales. Configura HTTPS/CSRF de acuerdo con tu proxy.

No uses varios procesos o réplicas: los resultados viven en la memoria de uno solo.
El análisis está limitado a uno simultáneo; las peticiones concurrentes reciben
un mensaje de espera y pueden reintentarse. Para escalar, diseña un almacén compartido
con expiración y una cola de análisis, conservando las garantías de privacidad.

## English

Áurea Lab is a bilingual, open-source image geometry analyzer. It reports **candidate**
golden rectangles and isolated logarithmic spiral strokes, with measurements and
downloadable overlays. It does not prove artistic intent or find every relationship
in arbitrary photographs. Run the Django application using the commands above;
select English in the header. No database, account or application JavaScript is needed.

Original author: David (DavidOrtegaH). MIT licensed; retain the copyright and license.
