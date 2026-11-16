# Golden Ratio Tester

He creado Golden Ratio Tester para comprobar las espirales áureas que se superponen
a tantas imágenes, especialmente a raíz del Spin de *JoJo’s Bizarre Adventure:
Steel Ball Run*. Quería poder subir o pegar una imagen, medir qué encaja y ver el
resultado sobre la propia imagen.

La aplicación busca encuadres, rectángulos y tramos de espiral compatibles con la
proporción áurea. Muestra cuántos candidatos encuentra, sus medidas y las guías,
que se pueden ocultar o descargar en un PNG. Está en español e inglés y recuerda
el idioma elegido. La selección, el análisis y el resultado comparten una página;
con los scripts disponibles, tampoco hace falta recargar para cambiar de idioma,
ocultar guías o borrar la imagen.

## Lo que he aprendido, cómo lo he resuelto y qué he conseguido

### Lo que he aprendido

La primera dificultad ha sido definir qué significa encontrar una proporción
áurea en una imagen. Una espiral que queda bonita encima de una foto no basta.
He trabajado con contornos, ajustes geométricos y medidas de error, y he visto
por qué una prueba con un dibujo limpio no demuestra que el detector funcione
igual en una fotografía.

También he trabajado con Django, procesamiento de imágenes en Python y una
interfaz con TypeScript y Stimulus. El proyecto me ha servido para practicar
la validación de archivos, la protección de formularios, la accesibilidad,
los estados de espera y las pruebas de casos que deben dar negativo.

### Cómo lo he resuelto

He separado la selección de la imagen, el análisis y la presentación del
resultado. El servidor comprueba el archivo y su tamaño antes de procesarlo;
la interfaz conserva la imagen mientras llega la respuesta y muestra los
resultados sin cambiar de pantalla. Los formularios normales siguen como
alternativa cuando el navegador no puede usar el flujo dinámico.

Para ampliar el detector he combinado trazos aislados, contornos y búsqueda
sobre bordes fragmentados. Después compruebo el crecimiento y el apoyo real de
la curva en la imagen. He añadido pruebas sintéticas, fotografías de control y
una evaluación antes/después para poder distinguir las mejoras de las limitaciones.

### Qué he conseguido

Tengo una herramienta bilingüe que permite subir o pegar imágenes, revisar
candidatos medidos y descargar las anotaciones. El detector ampliado encuentra
tramos en casos con textura y en una fotografía de una concha que la primera
versión no detectaba. La entrada de imágenes está limitada, los resultados
caducan y las pruebas cubren tanto el recorrido habitual como errores de
subida, seguridad y conexión.

Aun así, hay fotografías y diagramas que siguen sin producir coincidencias.
Prefiero dejar esas limitaciones documentadas y continuar mejorando el detector
con ejemplos que se puedan comprobar.

## Cómo usarla

1. Selecciona un JPG, PNG o WebP, o copia una imagen y pégala con **Ctrl+V / ⌘V**.
2. Revisa la vista previa y pulsa **Analizar imagen**. Pegar no la envía por sí solo.
3. Consulta los candidatos, muestra u oculta las guías y descarga el PNG.
4. Puedes cambiar de idioma, elegir otra imagen o eliminar el resultado desde la misma página.

El límite es de **10 MiB**, **20 megapíxeles** y **12.000 píxeles por lado**.
No se admiten imágenes animadas. Copiar la dirección de una imagen no equivale a
copiar la imagen. La exportación conserva la resolución y corrige la orientación
EXIF, pero elimina los metadatos.

## Qué mide y cuáles son sus límites

El recuento es de **candidatos geométricos aproximados**. No reconoce objetos ni
certifica la intención de una composición. Varios tramos pueden pertenecer a
una misma estructura y un resultado de cero no demuestra que no haya ninguna relación.

- Rectángulos: relación entre lados a menos del 3% de φ, con ángulos próximos a 90°.
- Espirales: crecimiento libre próximo al de la espiral áurea; se comprueban el
  recorrido, el error y, en contornos y bordes, al menos un 72% de apoyo con orientación compatible.
- El crecimiento mostrado es el factor del radio por cada cuarto de vuelta;
  el objetivo es **φ ≈ 1,618**. Los distintos errores no son probabilidades.

El análisis trabaja con versiones reducidas de hasta 1200, 800 o 640 píxeles,
según el método, y tiene un presupuesto de búsqueda limitado. Puede omitir
coincidencias pequeñas o difíciles de separar. La perspectiva, la textura y
las oclusiones siguen influyendo en el resultado.

He dejado los criterios y los resultados en [las especificaciones](specs/) y
[el informe del detector](docs/detector-evaluation.md). Las fotografías de terceros
conservan sus propias licencias y no se incluyen en el repositorio.

## Stack

Python 3.12+, Node 22.22.2+ o 24.15+ para desarrollo, Django 5.2 LTS, OpenCV, NumPy, SciPy, scikit-image y Pillow.
La interfaz usa plantillas Django, Bootstrap, Sass, TypeScript y Stimulus.
Los scripts se compilan con esbuild. No hace falta una base de datos ni una cuenta.

## Arranque local

Desde PowerShell, dentro de la carpeta del proyecto:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.lock
npm.cmd ci
npm.cmd run build
$env:DJANGO_DEBUG='1'
.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

Después abre [localhost:8000](http://127.0.0.1:8000).
En Linux o macOS usa `.venv/bin/python`, `npm` y `export DJANGO_DEBUG=1`.
El CSS y el script compilados están versionados; Node se necesita para modificarlos.

## Privacidad y seguridad

Las imágenes se procesan en el servidor que ejecuta la aplicación y se guardan
solo en memoria durante un máximo de 15 minutos. Se pueden borrar antes y pueden
caducar si el servidor se reinicia o se alcanza el límite de 32 resultados o
192 MiB. Quien tenga la dirección privada de un resultado puede verlo mientras exista.

El servidor valida el contenido, limita el cuerpo de las peticiones y los
archivos durante la recepción, restringe los formatos y vuelve a codificar las
imágenes. Los formularios usan CSRF y las respuestas incluyen CSP y `no-store`.
Los registros de la aplicación ocultan los identificadores de los resultados.

Se permiten seis intentos de análisis por minuto y conexión, con un solo análisis
simultáneo. El limitador conserva un identificador temporal, no la dirección en
claro, durante un minuto como máximo. No utiliza cabeceras de proxy sin verificar.
Detrás de un proxy puede agrupar varios usuarios; hay que configurar también los
límites del alojamiento según su red.

| Cookie propia | Para qué sirve | Duración |
| --- | --- | --- |
| `csrftoken` | Proteger los formularios | Sesión del navegador |
| `golden_ratio_tester_language` | Recordar el idioma elegido | 180 días |

No hay publicidad, analítica ni recursos externos durante el uso de la aplicación.
La cookie del idioma se guarda tras una elección explícita y se borra desde
«Privacidad y cookies». Una elección guardada con el nombre antiguo de la cookie
se recupera y se sustituye cuando se vuelve a seleccionar el idioma.

Antes de abrir una instancia pública hay que completar la identificación y el
contacto de su responsable y adaptar la información de privacidad al alojamiento.

## Comprobaciones

```powershell
$env:DJANGO_DEBUG='1'
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py test -v 2
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
```

Las pruebas actuales incluyen 33 casos de backend y 11 de interfaz.
La integración continua repite estas comprobaciones y la suite de navegador. La auditoría y la matriz de
compatibilidad comprobada se documentan en [el informe de revisión](docs/audit-2026-11-17.md).
Para probar Chromium, Firefox y WebKit con el servidor de pruebas aislado:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH=Join-Path (Get-Location) 'artifacts/playwright-browsers'
npx.cmd playwright install chromium firefox webkit
npm.cmd run test:e2e
```

La suite utiliza el puerto 8001 y no modifica la instancia del puerto 8000.
Las pruebas de desarrollo no equivalen a una tasa de acierto sobre todas las fotografías.

Para reproducir la evaluación del detector:

```powershell
.venv/Scripts/python.exe scripts/evaluate_detector.py
```

## Alojamiento

El repositorio contiene una aplicación Python; GitHub Pages no ejecuta este backend.
En producción `DJANGO_DEBUG` está desactivado por defecto y debe establecerse una
clave `DJANGO_SECRET_KEY` larga y aleatoria y la lista exacta `DJANGO_ALLOWED_HOSTS`.
[.env.example](.env.example) muestra las variables, que deben configurarse en el
entorno del servicio; ese archivo no se carga automáticamente.

Hay que servir los estáticos con el proxy después de ejecutar `collectstatic`,
poner HTTPS y un límite de cuerpo de 11 MiB, y evitar registrar direcciones
completas de resultados también en el proxy. El servidor de desarrollo no sirve
para publicar la aplicación.

Ejemplo de un único proceso Waitress **detrás de un proxy HTTPS**, con el backend
restringido a loopback:

```powershell
.venv/Scripts/waitress-serve.exe --listen=127.0.0.1:8000 --threads=4 --url-scheme=https golden_ratio_tester.wsgi:application
```

El almacén y los límites viven en un proceso. Para usar varias réplicas hace falta
un almacén compartido con caducidad y una estrategia común de límites y trabajos.
HSTS para subdominios y preload deben decidirse con el dominio real.
La excepción de `Origin: null` está restringida al desarrollo HTTP local con
cliente y host en loopback; producción conserva la comprobación estricta.

## Desarrollo y licencia

Uso SpecDD: primero documento el comportamiento, después lo implemento y lo
compruebo. Las ramas son `feature` → `develop` → `release` → `main` y los commits
siguen Conventional Commits en inglés. Los pasos para contribuir están en
[CONTRIBUTING.md](CONTRIBUTING.md).

Autor original: **David ([@DavidOrtegaH](https://github.com/DavidOrtegaH))**.
Código abierto bajo [MIT](LICENSE). Las copias del código deben conservar el
aviso de autoría y la licencia.
