# Publicación en GitHub Pages

Aplicación: https://davidortegah.github.io/golden-ratio-tester/

GitHub Pages sirve archivos estáticos. La aplicación publicada ejecuta el
detector compartido de `lab/geometry.py`, `contours.py` y `templatesearch.py`
mediante Python/WebAssembly en un worker. Django continúa disponible como
alternativa para desarrollo local o un servidor Python; no se ejecuta en Pages.

## Preparación y despliegue

`npm run build` compila los estilos y scripts de Django. `npm run build:pages`
prepara `artifacts/pages`, renderiza la misma plantilla, genera el paquete del
detector y compila la interfaz Stimulus y el worker. El sitio usa rutas relativas
para funcionar bajo `/golden-ratio-tester/`.

El workflow `.github/workflows/pages.yml` construye la aplicación, comprueba
tipos, ejecuta las pruebas de interfaz y la matriz de navegador, sube el artefacto
y lo publica mediante el entorno `github-pages`. Solo el trabajo de despliegue
recibe permisos `pages: write` e `id-token: write`. Se conserva la política de
seguridad existente de Actions del repositorio.

La configuración de Pages usa `build_type: workflow` y HTTPS. No hay claves de
aplicación, servicios de análisis, bases de datos ni dominios externos necesarios
en tiempo de ejecución.

## Motor fijado y perfil de dependencias

`pages/runtime-lock.json` fija Pyodide 314.0.8 y los hashes SHA-256 de los
archivos oficiales y wheels sin modificar. El build verifica todos los hashes,
incluida la caché local, antes de preparar el artefacto. Una actualización requiere
revisar los cambios y ejecutar explícitamente `scripts/build_pages.py --lock-runtime`.

El perfil `pages/package-profile.json` limita scikit-image a la ruta utilizada:
`morphology.skeletonize`. Conserva NumPy, SciPy, packaging y lazy-loader, además
de OpenCV. No se distribuyen Pillow, imageio, matplotlib, networkx ni pywavelets.
Se utiliza un registro de carga de Pyodide derivado para ese perfil; el manifiesto
público incluye su hash por separado. Los wheels se conservan intactos. Añadir
otros módulos de scikit-image exige revisar y ampliar el perfil y repetir pruebas.

El navegador decodifica JPG/PNG/WebP y normaliza los píxeles antes de pasarlos a
Python; el worker nunca recibe archivos comprimidos ni ejecuta código del usuario.
El detector recibe hasta 1200 píxeles por lado. El reescalado nativo del navegador
y las versiones WebAssembly pueden producir pequeñas diferencias frente a Pillow
y las bibliotecas nativas de la versión Django.

`THIRD_PARTY_NOTICES.txt` en el artefacto reúne avisos de licencia incluidos en los
wheels, junto con los enlaces de Pyodide y CPython. La licencia MIT del proyecto
no sustituye las licencias de esos componentes.

## Seguridad, privacidad y límites

- En Pages, el cálculo se realiza en el navegador y las peticiones de red del
  flujo de análisis son GET de archivos del mismo origen. Django utiliza su
  propio servidor de procesamiento cuando se ejecuta esa variante.
- Solo se crea una cookie de idioma tras una elección explícita. Su ámbito es
  el subdirectorio del proyecto; `SameSite=Lax`, `Secure` en HTTPS y 180 días.
  Se elimina desde el apartado de privacidad. No hay cookie CSRF en Pages.
- GitHub recibe datos técnicos al servir el sitio; la política de GitHub sigue
  siendo aplicable. No se promete ausencia de registros del proveedor.
- CSP en meta: recursos propios, imágenes blob, worker propio, ejecución WASM;
  sin código inline, `eval` general ni formularios de red. Pages no permite
  configurar cabeceras HTTP arbitrarias: la CSP meta no impone frame-ancestors
  ni sustituye las cabeceras configurables de un servidor propio.
- Tipos, tamaño de 10 MiB, animación y dimensiones se validan. La decodificación
  nativa ocurre antes de poder comprobar las dimensiones; un dispositivo con
  poca memoria puede cerrar la pestaña. No se garantiza resistencia ilimitada
  a imágenes patológicas ni a errores del decodificador del navegador.
- El cálculo tiene un límite de tres minutos y se puede cancelar terminando el
  worker. No bloquea el hilo de la interfaz. Se descartan respuestas antiguas.
- Los resultados caducan a los 15 minutos y sus URL blob se revocan al eliminar,
  sustituir o cerrar. No hay enlaces públicos a los resultados.
- La descarga PNG conserva la resolución normalizada y no copia EXIF ni texto
  del archivo original. Los navegadores pueden añadir metadatos propios del PNG.

La primera carga descarga el motor (el tamaño exacto se calcula durante el build).
El análisis puede tardar más en móviles y con archivos complejos. Requiere
JavaScript, WebAssembly y workers de tipo módulo; no se admite Internet Explorer.
Con JavaScript desactivado se explica la limitación y se bloquean los formularios.

## Verificación

`npm run test:pages` prueba el artefacto bajo el subdirectorio real, en Chromium,
Firefox y WebKit: detección real de rectángulo y espiral, ningún POST ni solicitud
externa durante el análisis, idiomas y cookie, guías, descarga PNG de 320×240,
borrado, pegado por evento, archivo inválido y cancelación de una carga atascada.
Comprueba anchos de 390, 768 y 1280 píxeles y analiza reglas axe WCAG A/AA.

Estas pruebas no equivalen a verificar todos los teléfonos físicos, portapapeles
de cada sistema operativo ni tecnologías de asistencia. El detector sigue siendo
heurístico y no certifica intención artística ni ausencia de proporción áurea.

Referencias oficiales: [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site),
[Pyodide en workers](https://pyodide.org/en/stable/usage/webworker.html).
