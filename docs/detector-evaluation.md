# Evaluación del detector ampliado — 15 de noviembre de 2026

Comparación contra el detector del commit `34aec20`. Los resultados actuales
completos, métricas y tiempos están en [detector-results.json](detector-results.json).
Se reproduce con `python scripts/evaluate_detector.py --photos artifacts/photo-validation`.
Sin `--photos` se ejecutan los casos locales de scikit-image y los sintéticos.

| Caso | Anterior | Ampliado | Interpretación |
| --- | ---: | ---: | --- |
| Espiral conocida, ruido y línea cruzada | 0 | 1 | Positivo sintético |
| Espiral conocida sobre fotografía de café | 0 | 1 | Montaje sintético, no fotografía natural positiva |
| camera / coffee / astronaut / chelsea | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | Controles fotográficos sin etiquetado exhaustivo |
| Concha de Suyothami | 0 | 2 | Dos tramos candidatos sobre bordes visibles; no prueba sobre toda la concha |
| Escalera de Ontario | 0 | 0 | No se encontró un candidato; no demuestra ausencia |
| Escalera de Brad Hammonds | 0 | 0 | No se encontró un candidato; no demuestra ausencia |
| Obra luminosa de Marinelli / Schettina | 0 | 0 | Caso no resuelto por el detector |

En la concha, los factores de crecimiento por 90° fueron 1,5907 y 1,6239
(objetivo 1,6180); el apoyo de bordes fue 80,4% y 94,2%. Se revisaron visualmente
las superposiciones. Se cuentan **tramos**, que pueden pertenecer a una estructura.
No hay segmentación semántica, medida física del objeto ni corrección de perspectiva.

Las 19 pruebas automatizadas pasan. Incluyen el flujo original, ambos sentidos
de giro, fondo con textura y cruce, montaje sobre fotografía, y rechazo de círculos,
espirales arquimedianas, crecimiento no áureo y cuadrículas. Esos cuatro patrones
geométricos negativos dieron cero espirales. Los cuatro controles fotográficos
también dieron cero; carecen de anotaciones exhaustivas y no permiten calcular
una tasa científica de falsos positivos. No hay conjunto independiente de prueba:
estos son casos de desarrollo y regresión usados para ajustar la implementación.

Los tiempos observados estuvieron entre 0,8 y 19,9 segundos por imagen en esta
máquina, con pruebas concurrentes. La concha tardó aproximadamente 2,8 segundos.
No es una garantía de latencia en otro servidor. La búsqueda tiene límites
explícitos y puede omitir coincidencias pequeñas, distantes del centro o con fuerte
perspectiva. Las dos referencias originales con guías siguen sin dar espirales
en esta versión; conservan sus candidatos rectangulares.

## Fuentes y licencias

Las fotografías externas no se incluyen en Git. Descarga el archivo original
desde su página y guárdalo con el nombre indicado para reproducir la evaluación.
Sus títulos no se usan como etiqueta de verdad matemática.

- `shell.jpg`: [Golden spiral on a shell](https://commons.wikimedia.org/wiki/File:Golden_spiral_on_a_shell.jpg), Suyothami, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- `ontario.jpg`: [Golden Spiral](https://commons.wikimedia.org/wiki/File:Golden_Spiral.jpg), Ian Muttoo, [CC BY-SA 2.0](https://creativecommons.org/licenses/by-sa/2.0/).
- `hammonds.jpg`: [Golden Spiral by Brad Hammonds](https://commons.wikimedia.org/wiki/File:Golden_Spiral_by_Brad_Hammonds.jpg), Brad Hammonds, [CC BY 2.0](https://creativecommons.org/licenses/by/2.0/).
- `light-art.jpg`: [Goldene Spirale Rotgelb](https://commons.wikimedia.org/wiki/File:Goldene_Spirale_Rotgelb.jpg), Marinelli; obra de Martina Schettina, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
- Los cuatro controles y el fondo del montaje proceden de [`skimage.data`](https://scikit-image.org/docs/stable/api/skimage.data.html), que documenta sus autores y condiciones. Los montajes añaden una curva sintética conocida, no perteneciente a la foto original.

Las superposiciones sobre fotografías externas son transformaciones: añaden
anotaciones y pueden reducir resolución; conservan la licencia aplicable de la
imagen base. La licencia MIT del código no sustituye las licencias de esas fotos.
