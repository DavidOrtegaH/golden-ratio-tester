# Golden Ratio Tester

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
- Pega una imagen con Ctrl+V / ⌘V, con vista previa local.
- Interfaz responsive con formularios estándar y mejora progresiva con TypeScript + Stimulus.
- Elimina imágenes al pulsar el botón o al expirar el plazo de 15 minutos.

## Qué NO demuestra

El número es un **recuento de candidatos bajo criterios concretos**, no un número
universal de todas las relaciones áureas de una fotografía. La versión inicial
no reconoce objetos semánticamente ni decide si una composición artística es áurea.

Un rectángulo admite hasta un 3% de desviación respecto a φ y debe tener ángulos
aproximadamente rectos. No se inventan recortes arbitrarios. Las dos caras del
borde de un mismo rectángulo se deduplican por solapamiento.

Las espirales se buscan por tres rutas: trazos aislados, tramos de contornos Canny
a dos escalas y una búsqueda de plantillas sobre bordes fragmentados. Se ajusta el
crecimiento libre de `r = a·exp(b·θ)` antes de aceptar su proximidad al crecimiento
áureo `|b| = 2·ln(φ)/π` (desviación máxima de b: 8%). No basta con dibujar una guía.

Los contornos requieren al menos media vuelta, crecimiento de radio ≥2,3,
error RMS radial libre ≤1,2% y error del ajuste áureo ≤1,8% de su diagonal.
En contornos y bordes se exige que ≥72% de los puntos del arco estén próximos a
bordes con orientación compatible, con al menos 40% de apoyo en cada octavo.
La búsqueda por plantillas exige una vuelta completa y distancia RMS a bordes
≤1,2%. Se muestran por separado el error de lados, el RMS radial y el RMS a bordes;
no son probabilidades. El crecimiento mostrado es el factor de radio por cada 90°,
cuyo objetivo es φ. Distintos tramos pueden pertenecer a una misma estructura.

El análisis general usa hasta 1200 píxeles en su lado mayor; contornos fotográficos
usan hasta 800 y plantillas hasta 640. Hay límites de 300 contornos rectangulares,
24 componentes de trazo, 50 contornos por escala, 160 optimizaciones por escala y
48 refinamientos de plantillas. La búsqueda cubre ambos sentidos, varios centros,
escalas y orientaciones; es acotada y puede omitir coincidencias. Los tiempos
medidos y los casos fallidos están en [el informe de evaluación](docs/detector-evaluation.md).

Las texturas, la perspectiva y las oclusiones siguen pudiendo impedir detecciones.
No hay reconocimiento semántico de objetos ni demostración de intención artística.
Un rectángulo no implica una espiral y cero candidatos no demuestra ausencia.
Las aproximaciones de Fibonacci con arcos de circunferencia tampoco son exactamente
la espiral logarítmica áurea.

## Stack

Python 3.12+, Django 5.2 LTS, OpenCV, NumPy, SciPy, scikit-image y Pillow.
Interfaz con plantillas Django, Bootstrap 5 y Sass. Pegado con TypeScript y Stimulus,
compilado mediante esbuild. No requiere base de datos.
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
El CSS y el script compilados están versionados; Node se necesita al modificar
Sass o TypeScript. `npm run build` recompila ambos.
En Linux/macOS sustituye `.venv/Scripts/python.exe` por `.venv/bin/python` y `npm.cmd` por `npm`.

## SpecDD y comprobación

La especificación se escribió y confirmó antes de la implementación:
[`specs/001-golden-analysis.md`](specs/001-golden-analysis.md).

```powershell
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py test -v 2
npm.cmd run build
```

Las 19 pruebas cubren positivos y negativos sintéticos, ambos sentidos de giro,
deduplicación, subida inválida, idiomas, CSRF, descarga, eliminación y caducidad.
Incluyen controles fotográficos y un montaje con curva conocida sobre fotografía.
No equivalen a una evaluación estadística del detector sobre fotografías reales.
La evaluación reproducible se ejecuta con `python scripts/evaluate_detector.py`
y admite fotografías locales opcionales mediante `--photos <carpeta>`.
También se verificó el flujo HTTP real contra el servidor local: selección de
idioma, CSRF con origen válido, subida, análisis, ocultación de guías, descarga
PNG y eliminación. Todos estos pasos pasaron.
El pegado tiene además 4 pruebas de eventos/UI en jsdom y comprobación de tipos:
`npm test` y `npm run typecheck`. Se verificaron en el navegador integrado Ctrl+V, la vista previa y el envío nativo hasta obtener un resultado.
CI ejecuta estas comprobaciones y verifica los dos archivos compilados.

Ramas: `feature` → `develop` → `release` → `main`. Conventional Commits en inglés.
Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

### Compatibilidad

Diseñado para versiones actuales de Chrome, Edge, Firefox y Safari, incluyendo
navegadores móviles. Seleccionar archivos y analizar funciona sin JavaScript.
El pegado usa el evento paste de la acción explícita Ctrl+V / ⌘V.
Se indica en texto dentro de la misma zona de selección, sin botón de pegar.
Copiar un enlace no copia la imagen.
Se han comprobado anchuras de 390 y 768 píxeles en el navegador integrado sin
desbordamiento horizontal. **La matriz de navegadores externos y dispositivos
físicos todavía no está verificada.** Los formularios del navegador integrado
con `Origin: null` se admiten únicamente en desarrollo HTTP local: DEBUG activo,
host local y conexión desde loopback. La cookie y el token CSRF siguen siendo
obligatorios. En producción y para otros clientes se conservan las verificaciones
estrictas de Django. Se usa `Referrer-Policy: same-origin` para permitir formularios
HTTPS sin Origin y evitar filtrar URLs de resultados a sitios externos.

## Pegar una imagen

Copia una imagen (opción «Copiar imagen» del navegador) o una captura de pantalla,
vuelve a la página principal y pulsa Ctrl+V / ⌘V.
Revisa la vista previa y pulsa «Analizar imagen». Pegar no sube la imagen por sí solo.
La selección de archivos sustituye a lo pegado, y pegar sustituye al archivo anterior.
Los límites y validaciones del servidor son los mismos para ambas opciones.
No se leen textos, enlaces ni historial del portapapeles; solo la imagen de la acción
explícita de pegar. La vista previa es una URL local temporal.

## Privacidad y cookies

Las imágenes se envían al servidor local que ejecuta la aplicación, se decodifican
y se mantienen solo en memoria. No se envían a proveedores de IA ni se usan para
entrenamiento. El almacén admite hasta 32 resultados y 192 MiB de PNGs normalizados y anotados;
los resultados antiguos pueden expulsarse antes de 15 minutos. Se usa un token
aleatorio de acceso: quien tenga la URL puede ver ese resultado mientras exista.
Las respuestas incluyen `no-store`, `same-origin`, CSP y exclusión de indexación.

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

La comprobación de producción realizada dejó dos avisos deliberadamente pendientes:
HSTS para todos los subdominios y HSTS preload. Deben decidirse con el dominio real;
no se activan de forma indiscriminada desde este proyecto.

No uses varios procesos o réplicas: los resultados viven en la memoria de uno solo.
El análisis está limitado a uno simultáneo; las peticiones concurrentes reciben
un mensaje de espera y pueden reintentarse. Para escalar, diseña un almacén compartido
con expiración y una cola de análisis, conservando las garantías de privacidad.

## English

Golden Ratio Tester is a bilingual, open-source image geometry analyzer. It reports **candidate**
golden rectangles and isolated logarithmic spiral strokes, with measurements and
downloadable overlays. It does not prove artistic intent or find every relationship
in arbitrary photographs. Run the Django application using the commands above;
select English in the header. No database or account is needed. Clipboard input uses TypeScript + Stimulus;
file uploads also work without client scripts.

Original author: David (DavidOrtegaH). MIT licensed; retain the copyright and license.
