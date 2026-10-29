# Metodología

Estas son las notas técnicas del proyecto: de dónde sale cada dato, qué decisiones tomé al procesarlo y dónde el análisis tiene puntos flojos. El resumen de hallazgos y las instrucciones para correr todo están en el [README](../README.md) — acá va el detalle que sostiene cada número.

Va organizado en una sección por núcleo (fuentes, metodología, supuestos y limitaciones), más un apéndice al final con fuentes que evalué y descarté para el Núcleo 1.

## Alcance: qué se mide y qué no

El objeto del trabajo son las transferencias **automáticas** de la Ley 23.548: las que el Banco Nación gira a diario a cada jurisdicción según su coeficiente, sin una decisión caso por caso. Con la definición del Núcleo 1, eso incluye el Financiamiento Educativo de la Ley 26.075, la compensación del Consenso Fiscal y, hasta 2017, las asignaciones específicas de Ganancias que después pasaron a repartirse por la Ley 23.548.

Quedan afuera, salvo donde se dice lo contrario:

- Las transferencias **no automáticas** o discrecionales (ATN, convenios, obras, programas). Solo aparecen en la comparación entre provincias del Núcleo 4, dentro de las transferencias corrientes y de capital de la ejecución presupuestaria.
- Los demás regímenes automáticos con leyes propias (IVA de la Ley 23.966, Bienes Personales, combustibles, entre otros).
- El gasto nacional directo en cada provincia, la previsión social y los impuestos que no se coparticipan, salvo la estimación de retenciones de Córdoba del Núcleo 2.

Las series en el tiempo están en pesos del promedio de 2025, con el IPC empalmado del Núcleo 1. Los escenarios puntuales usan los pesos de su período: el Núcleo 3, pesos de enero-abril de 2026. El CSV del Núcleo 1 conserva además la columna en pesos de 2016, que es la base con la que se construye el empalme.

## Cómo conseguí los datos

Todos los archivos de `data/raw/` los descargué o los conseguí a mano y los versioné tal cual, así el proyecto se reproduce sin acceso a internet. La trazabilidad de cada archivo (de dónde salió, qué alcance tiene, por qué lo usé o lo descarté) está en [`data/raw/README.md`](../data/raw/README.md).

---

## Núcleo 1 — Serie histórica de coparticipación (2003-2025)

### Fuentes

- **Coparticipación federal / Recursos de Origen Nacional (RON)**: Secretaría de Hacienda, Ministerio de Economía de la Nación. <https://www.argentina.gob.ar/economia/sechacienda/asuntosprovinciales/ron>. Archivo: `data/raw/coparticipacion/serie_ron_2003_2025.csv` (2003-2025).
- **IPC 2016-2025**: INDEC. <https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv>. Archivo: `data/raw/ipc/serie_ipc_divisiones.csv` (mensual, desde dic-2016).
- **IPC 2003-2015**: Fundación Norte y Sur / Orlando J. Ferreres, conseguida en forma directa (sin URL pública verificada). En el repositorio está solo lo que uso: las 14 tasas de variación anual del empalme, transcriptas de la hoja `IPC ` del archivo original, en `data/raw/ipc/ferreres_variaciones_usadas.csv`. El archivo completo es una compilación de series desde ~1810 y no lo redistribuyo. Es la compilación histórica de series económicas de Argentina que hizo Ferreres para la Fundación Norte y Sur (conocido por *"Dos siglos de Economía Argentina"*) — la uso como insumo de análisis, sin reclamar autoría sobre la compilación.

- **PIB nominal y a precios de 2004**: INDEC, cuentas nacionales (año base 2004), cuadros de oferta y demanda globales. <https://www.indec.gob.ar/ftp/cuadros/economia/sh_oferta_demanda_09_26.xls>. Archivo: `data/raw/pib_nacional/sh_oferta_demanda_09_26.xls`, columnas anuales de 2004 a 2025 (no tiene 2003).
- **Población por jurisdicción**: INDEC, censos 2001, 2010 y 2022. El Censo 2022 (`data/raw/poblacion/c2022_tp_est_c1.xlsx`) trae también la población 2010; la de 2001 la transcribí del Cuadro 8 del Tomo 1 de resultados definitivos del Censo 2010 (<https://www.indec.gob.ar/ftp/cuadros/poblacion/censo2010_tomo1.pdf>, página 64), en `data/raw/poblacion/censos_2001_2010_cuadro8.csv`. La transcripción suma el total del país en los dos años y su columna 2010 coincide persona por persona con la del Censo 2022; las dos cosas las controla un test.

Incorporé estos datos el 20 de agosto de 2026 (con el rango original acotado a 2016-2025), y amplié a 2003-2025 el 12 de septiembre.

### Metodología

El archivo de RON desagrega lo transferido a cada provincia en unos 14 conceptos (coparticipación Ley 23.548, Financiamiento Educativo, IVA, Ganancias, Bienes Personales, combustibles líquidos, régimen simplificado, etc.). Definí "coparticipación" como la coparticipación Ley 23.548 **bruta**, más la compensación del Consenso Fiscal (Ley 27.429, desde 2018), más, hasta 2017, las asignaciones específicas de Ganancias. Las dos piezas que no son obvias:

- **Bruto o neto.** Hacienda informa la Ley 23.548 de dos maneras según el año: como monto bruto ("coparticipación federal de impuestos Ley 23.548", en 2003-2005 y 2011) o como monto neto de la parte que la Ley 26.075 afecta a educación ("neta Ley 26.075"), con esa parte en un concepto aparte ("financiamiento educativo Ley 26.075", en 2006-2010 y 2012-2025). En una primera versión traté el bruto y el neto como el mismo concepto. Era un error: el Financiamiento Educativo no se reparte con los coeficientes, pesa entre 5% y 33% de lo que recibe cada jurisdicción (en 2025, sobre el total que recibe incluida la compensación del Consenso Fiscal: 5% en Tierra del Fuego, 13% en Córdoba, 21% en Buenos Aires, 33% en CABA), y cada cambio de forma metía un salto falso, como el "pico" de 2011. Ahora sumo el neto y el Financiamiento Educativo. Un test (`test_bruto_y_neto_mas_financiamiento_educativo_son_el_mismo_concepto`) verifica que con esa suma la participación de cada jurisdicción no salte al cambiar de forma (menos de 0,25 puntos por año en 2003-2015; con solo el neto, saltaba hasta 1,7 puntos).
- **Ganancias hasta 2017.** Hasta 2017, una parte de Ganancias se repartía por fuera de la Ley 23.548: el Fondo de Infraestructura Básica Social para las provincias y el Fondo del Conurbano para Buenos Aires (concepto "impuesto a las ganancias" en RON). El Consenso Fiscal (Ley 27.429, punto I.c) eliminó esas asignaciones y desde 2018 esa plata entra por la Ley 23.548. Sin sumarla antes de 2018, la serie tendría un quiebre de ~17% en ese año en todas las provincias salvo Buenos Aires (cuyo fondo estaba congelado) y CABA (que no lo recibía). La sumo hasta 2017, y el script corta si el concepto aparece después de ese año.

Dejé afuera el resto de los conceptos de RON (IVA de la Ley 23.966, Bienes Personales, combustibles, régimen simplificado, etc.): son regímenes de distribución relacionados, pero distintos de la coparticipación Ley 23.548.

El archivo fuente también trae filas que no son provincias (`fdo.compensador`, `fondo a.t.n.`, `seguridad social`, `tesoro nacional`) — las excluí, así que el análisis queda en 23 provincias + CABA.

Para deflactar uso `monto_real = monto_nominal × (IPC_promedio_2016 / IPC_promedio_año)`, en pesos constantes del promedio de 2016. Para 2017-2025 uso `serie_ipc_divisiones.csv` filtrado a `Region == "Nacional"` y `Descripcion == "NIVEL GENERAL"`, promediando los 12 valores mensuales. Ese IPC oficial arranca en diciembre de 2016, así que no tiene un promedio 2016 propiamente dicho. En una primera versión usé diciembre como si fuera el promedio, y eso sesgaba la serie: diciembre está ~10% por encima del promedio del año, así que todos los valores reales de 2003-2016 quedaban subestimados en esa proporción y cualquier crecimiento que cruzara 2016→2017 salía inflado en esa misma proporción. Ahora estimo el promedio de 2016 como el promedio oficial de 2017 dividido por (1 + la variación 2017 de la tabla de estimaciones privadas de Ferreres, 23,85%). Como control, esa misma tabla da 32,9% para 2018 contra 34,3% del IPC oficial nacional: no son idénticas (una es GBA y la otra nacional), así que el anclaje es una aproximación razonable, no exacta.

Para 2003-2015 tuve que empalmar dos series del archivo de Ferreres/Norte y Sur (función `load_ipc_empalmado` en `scripts/process_coparticipacion.py`), porque ninguna de las dos tablas del archivo sirve sola para todo el período: la tabla "GBA (INDEC)" es una serie continua desde ~1810, pero para 2007-2014 reproduce las mismas tasas bajas y desacreditadas del IPC oficial de la época (no está corregida para el período de intervención), así que solo la uso para 2004-2006. La tabla "GBA (estimaciones privadas)" cubre 2006-2025 con tasas mucho más altas para 2007-2015, consistentes con lo que estimaban las consultoras privadas en ese momento; la uso para 2007-2017.

El método es simple: parto del promedio 2016 estimado y encadeno hacia atrás, año por año, con las tasas de variación % anual tal como figuran en el archivo (no las recalculo desde niveles, para no meter redondeos propios): de 2015 a 2007 con la tabla de estimaciones privadas, de 2006 a 2003 con la tabla del INDEC. Con 2016 = 100, el resultado queda: 2003→8,40, 2004→8,77, 2005→9,61, 2006→10,66, 2007→12,19, 2008→14,98, 2009→17,46, 2010→21,38, 2011→26,57, 2012→32,79, 2013→40,85, 2014→56,98, 2015→73,66, 2016→100,00, 2017→123,85: una suba acumulada de ~11,9 veces entre 2003 y 2016, en línea con la inflación que efectivamente tuvo Argentina en ese período.

### Supuestos y limitaciones

No llega a 1990, que era la idea original: no encontré, en ninguna fuente, montos nominales de coparticipación por provincia para 1990-2002 — el archivo de RON arranca en 2003. El índice de precios en sí podría reconstruirse desde antes (la tabla de Ferreres llega a ~1810), pero sin montos nominales que deflactar no serviría de mucho. Confirmé con la fuente que no hay ese dato disponible.

Sobre el IPC oficial de 2007-2015: que subestimó la inflación real en ese período no es una discusión de opinión, es un hecho bastante documentado — la llamada "intervención del INDEC". El FMI censuró formalmente a Argentina en 2013 por la calidad de esos datos, y el propio INDEC, ya con otra gestión desde fines de 2015, declaró la "emergencia estadística" y discontinuó esos índices.

Una limitación que no pude resolver: las dos tablas del archivo de Ferreres marcan algunos años con asterisco (2015 y 2016 en la tabla del INDEC) y una nota "Ver metodología", pero el archivo que tengo no incluye ninguna hoja de metodología que explique ese ajuste. No sé qué significa exactamente, así que lo dejo anotado acá en vez de inventar una explicación.

Para Córdoba pude contrastar esta serie con una fuente independiente, el archivo de recaudación provincial del Núcleo 4: con la misma definición, las dos coinciden todos los años 2015-2025 con diferencias menores al 1,6%. Ese contraste fue lo que me permitió encontrar el quiebre de Ganancias en 2018 (el detalle está en la sección del Núcleo 4).

`scripts/process_coparticipacion.py` chequea que existan las 552 combinaciones esperadas (24 jurisdicciones × 23 años) y que haya IPC para cada año antes de deflactar. Hasta ahora no faltó ninguna; si faltara alguna, el script lo avisa y deja ese hueco vacío en vez de completarlo por su cuenta.

Los gráficos del notebook muestran los montos reales en pesos de 2025 (`nominal × ipc_2025 / ipc_año`), una unidad más fácil de dimensionar que pesos de 2016; es el mismo IPC, solo cambia el año de referencia. El CSV conserva la columna en pesos de 2016.

#### Por habitante, como % del PIB y año base

Un monto real que crece no dice si creció más o menos que la población o que la economía. Una versión anterior del proyecto destacaba que la coparticipación real de 2025 era 3,1 veces la de 2003. La cuenta estaba bien, pero el titular exageraba por tres motivos:

1. **El año base.** 2003 es el piso de la crisis de 2001-2002: solo en 2004 la serie sube 47% real. No es un quiebre de definición: la masa total de la Ley 23.548 que registra Hacienda (incluidos Nación y la ANSES) también sube 43% real ese año, por la recuperación de Ganancias y de IVA. Desde 2004, el crecimiento es de 2,14 veces. Antes había además un gráfico indexado a 2003 = 100 para comparar provincias; lo reemplacé por la coparticipación por habitante en niveles, porque el resultado del índice dependía del año base (con base 2004, Buenos Aires, que ese año todavía tenía el Fondo del Conurbano congelado, pasaba a ser la que más crecía).
2. **La población.** Entre 2004 y 2025 la población estimada creció 27%. Por habitante, el crecimiento es de 1,68 veces desde 2004 (2,44 desde 2003), y 2025 queda en el nivel de 2016.
3. **La economía.** Como % del PIB, la coparticipación de las 24 pasó de 4,9% en 2004 a 6,7% en 2025 (máximo de 7,5% en 2020, cuando el PIB cayó más que la recaudación).

**Población de cada año** (`scripts/poblacion.py`): entre dos censos, crecimiento a tasa constante entre las fechas censales (17 de noviembre de 2001, 27 de octubre de 2010 y 18 de mayo de 2022), evaluado a mitad de año. Después de 2022 extiendo la tasa 2010-2022 de cada jurisdicción. Es un supuesto: con la caída de la natalidad de esos años, la población 2023-2025 probablemente quede algo sobreestimada (para el total del país, 47,6 millones en 2025) y la coparticipación por habitante, algo subestimada. No hay en el repositorio proyecciones oficiales basadas en el Censo 2022.

**Descomposición** (`descomponer` en `scripts/build_coparticipacion_pib_poblacion.py`). Para el total de las 24, en términos reales vale la identidad

`coparticipación / IPC = PIB real × (deflactor del PIB / IPC) × (masa Ley 23.548 / PIB) × (coparticipación / masa)`

Entre 2004 y 2025 da: PIB real ×1,525; deflactor del PIB / IPC ×1,024; masa / PIB ×1,258; parte de la masa que llega a las 24 ×1,089; total ×2,139. Dividido por la población (×1,275), ×1,678 por habitante. Un test controla que el producto de los factores reproduzca el total. Tres lecturas:

- **No hay ilusión monetaria en la serie.** Deflactada por el deflactor del PIB en vez del IPC, crece ×2,09 en vez de ×2,14: el resultado no depende del índice de precios. Tampoco depende del empalme con Ferreres en 2007-2015, que sigue de cerca al deflactor implícito del INDEC en esos años.
- **La masa sobre el PIB (×1,26)** mezcla presión tributaria y una reclasificación: desde 2018 las asignaciones específicas de Ganancias entran por la Ley 23.548, y ese año la masa salta de 10,4% a 11,8% del PIB. Parte de la suba de la presión tributaria probablemente sea, a su vez, un efecto de la inflación (Ganancias sin ajuste por inflación recauda más en términos reales), pero eso no está medido en este repositorio.
- **La parte que llega a las 24 (×1,09).** Dentro de la Ley 23.548, la porción de las provincias pasó de 48% (2004) a 59% (2025), sobre todo por la devolución del 15% que se detraía para la ANSES (2016-2020). El factor queda en ×1,09 porque, con la definición de este núcleo, hasta 2017 las asignaciones de Ganancias llegaban a las provincias por fuera de la masa. En una primera lectura atribuí a la devolución de la ANSES cerca del 60% de la suba de la coparticipación como % del PIB; con la descomposición completa no se puede separar así, porque el mismo cambio de 2018 mueve los dos últimos factores en sentido contrario.

El PIB del INDEC arranca en 2004, así que el % del PIB y la descomposición no cubren 2003.

Scripts: `scripts/process_coparticipacion.py`, `scripts/poblacion.py` y `scripts/build_coparticipacion_pib_poblacion.py`. Notebook: `notebooks/01_serie_historica.ipynb`.

---

## Núcleo 2 — Aporte vs. recibo por provincia

### Fuentes

- **Producto Bruto Geográfico (PBG) por provincia**: CEPAL, sobre metodología base de INDEC (año base 2004). Archivo: `data/raw/pbg/Jurisdiccion_52sectores.xlsx` (hoja `VABpb`), 2004-2024. No es la publicación directa de INDEC (que en su archivo público solo llega a 2017) — es una actualización de CEPAL, la más reciente que encontré. En rigor es el Valor Agregado Bruto a precios básicos, en millones de pesos a precios de 2004; en el proyecto lo llamo PBG por simplicidad.
- **Derechos de exportación (retenciones)**: Secretaría de Hacienda, serie anual de recursos tributarios por tributo, descargada de la API de series de tiempo de datos.gob.ar (id `142.1_DEREC_2001_A_20`, millones de pesos corrientes). Archivo: `data/raw/fiscal_nacional/derechos_exportacion_anual.csv`.
- **Exportaciones por provincia y rubro**: INDEC (origen provincial de las exportaciones), misma API (ids `350.1_*`): total del país y Córdoba, en productos primarios, manufacturas de origen agropecuario, manufacturas de origen industrial y combustibles, 1993-2024. Archivo: `data/raw/exportaciones/exportaciones_cordoba_y_total_por_rubro.csv`.
- **Coeficientes de coparticipación (Ley 23.548)**: planilla "Índices de Distribución de la Coparticipación Federal de Impuestos y Regímenes Especiales de Distribución". El documento no indica qué organismo la emitió; menciona que el Banco de la Nación Argentina distribuye en base a notas instructivas de la Secretaría de Hacienda. Archivo: `data/raw/coeficientes/indices_copa_2018.pdf`, creado el 2 de febrero de 2018 según la metadata del archivo.

### Metodología

Trabajo con las 24 jurisdicciones en un solo corte (no serie temporal). "Aporta" es el % del PBG de cada provincia sobre la suma de las 24 jurisdicciones en 2024 (la fuente trae además una fila "No distribuido", ~0,06% del total, que dejo afuera para que las participaciones sumen 100%), el año más reciente disponible (dato preliminar en la fuente). "Recibe" es la porción de cada provincia en lo que se reparte **entre provincias**: su coeficiente de Ley 23.548 (con el ajuste de CABA que explico abajo) dividido por la suma de los 24 coeficientes. La métrica es la diferencia en puntos porcentuales (recibe − aporta): positivo significa que la provincia recibe una porción del reparto mayor que su peso económico, negativo lo contrario.

Qué mide y qué no: la coparticipación está diseñada para redistribuir, así que una brecha contra el PBG mide cuánto redistribuye el régimen y hacia dónde, no si el reparto es justo. Y la coparticipación es solo una parte de la relación fiscal de cada provincia con la Nación: quedan afuera los impuestos que no se coparticipan, el gasto nacional directo en cada provincia (por ejemplo, los subsidios a la energía y al transporte, concentrados en el AMBA), las transferencias no automáticas y la previsión social. El notebook lo explica antes de mostrar los resultados.

**Retenciones atribuibles a Córdoba** (`scripts/build_retenciones_cordoba.py`). De lo que queda afuera, lo más relevante para Córdoba son las retenciones, que van enteras al Tesoro Nacional. Las estimo para 2003-2024 repartiendo el total nacional de cada año según la participación de Córdoba en las exportaciones de productos primarios y manufacturas de origen agropecuario (15%-19% según el año), los rubros donde se concentran las retenciones. Como cota baja uso su participación en el total de las exportaciones (10%-15%). Resultado: en 2024, unos $1,48 billones (pesos de 2025; $1,08 billones con la cota baja), el 31% de la coparticipación de Córdoba (23% con la cota baja); en 2008 superaron a la coparticipación (126%) y en 2021-2022 fueron el 62%-67%. Sumando 2003-2024, equivalen al 59% de la coparticipación de esos años.

Scripts: `scripts/build_coefficients_comparison.py` y `scripts/build_retenciones_cordoba.py`. Notebook: `notebooks/02_aporte_vs_recibo.ipynb`.

### Supuestos y limitaciones

El documento de coeficientes es de febrero de 2018, no la versión más actual: el valor de CABA ahí (3,75%) corresponde al Decreto 194/2016. Lo reemplacé por 1,4%, el coeficiente del régimen automático vigente desde la Ley 27.606 (2020); los otros 23 coeficientes no los toqué, porque son la tabla de la Ley 23.548 de 1988 y no cambiaron. Hay un detalle más: en diciembre de 2022 la Corte Suprema dictó una cautelar que obliga a Nación a transferirle a CABA un 1,55% adicional (2,95% en total), y en 2025 Nación y la Ciudad acordaron cómo cumplirla. Ese 1,55% se paga por fuera del régimen automático, así que mantengo el 1,4% para ser coherente con la serie de transferencias del Núcleo 1, y en el notebook muestro cómo cambia el resultado con 2,95% (la brecha de CABA pasa de −17,5 a −15,0 pp; la de Córdoba, de +0,01 a −0,2 pp). Tampoco modelé la excepción de Córdoba, Santa Fe y San Luis a la detracción del 15% para ANSES (es un descuento sobre la masa antes del reparto, no un coeficiente distinto).

Los 24 coeficientes suman ~0,59, no 1: el resto es lo que retienen Nación y el Fondo ATN. Por eso los renormalizo antes de compararlos con el PBG, que suma 100% entre provincias. En una primera versión los comparé sin renormalizar y el resultado era engañoso: como el coeficiente crudo es una fracción de un total más grande, todas las provincias grandes quedaban con brechas negativas por el solo hecho de ser grandes (Córdoba aparecía con −3,5 pp, cuando su porción del reparto, 8,58%, es prácticamente igual a su peso en el PBG, 8,57%). Renormalizado, el ranking mide cómo se reparte entre provincias, que es la pregunta del núcleo; cuánto se queda Nación es otra pregunta.

El PBG de la fuente está a precios constantes de 2004, así que la participación de cada provincia en 2024 está calculada con los precios relativos de 2004. En provincias donde el precio de lo que producen cambió mucho respecto del resto (las petroleras, por ejemplo), la participación a precios corrientes podría ser distinta. La fuente no trae una serie a precios corrientes, así que no lo puedo cuantificar.

El ranking usa el coeficiente legal, no lo que cada jurisdicción efectivamente cobra. El Núcleo 5 muestra que la diferencia entre las dos cosas es casi toda la compensación del Consenso Fiscal; con la participación efectiva de 2025, la brecha de Buenos Aires baja de −10,7 a −9,2 puntos, la de Córdoba pasa de +0,01 a −0,3 y el resto se mueve menos de 0,15 puntos. El notebook muestra las dos versiones.

La estimación de retenciones es de orden de magnitud. Supone que todos los productos primarios y agroindustriales pagan la misma alícuota, cuando la soja y sus derivados pagaron bastante más que el maíz o el trigo: si Córdoba exporta relativamente más soja que el promedio del país, la estimación queda corta, y si exporta relativamente más maíz o maní, queda larga. El origen provincial de INDEC no siempre coincide con el lugar exacto de producción. Y quien soporta el impuesto (en buena medida el productor, vía un precio más bajo) no es necesariamente quien lo paga. No alcanza para calcular un residuo fiscal, porque falta el gasto nacional en la provincia.

El PBG como proxy del aporte tributario tiene un problema conocido: mide dónde se *genera* la actividad económica, no dónde se *paga* el impuesto. Las empresas grandes con operaciones en todo el país suelen tener domicilio fiscal en CABA, así que en las estadísticas de recaudación por jurisdicción buena parte de lo generado en otras provincias figura como pagado en CABA. Si usara esa recaudación en vez del PBG, CABA aparecería aportando todavía más y provincias productivas como Córdoba, menos. El PBG está más cerca de dónde se genera la actividad, pero no es una medición directa de lo que tributa cada provincia.

---

## Núcleo 3 — Simulador de sensibilidad

No tiene fuentes propias: reutiliza los coeficientes de coparticipación del Núcleo 2 (`scripts/coeficientes_ley23548.py`) y, para calibrar el escenario de referencia, la coparticipación nominal 2025 del Núcleo 1 sin la compensación del Consenso Fiscal.

### Metodología

El corazón es `simular_shock(variacion_pct_recaudacion, recaudacion_base, coeficientes_por_provincia)`, en `scripts/simulator.py`, con 9 tests automáticos en `scripts/test_simulator.py` (`pytest scripts/test_simulator.py`). `recaudacion_base` es la masa coparticipable TOTAL de referencia (incluye lo que retiene Nación y el Fondo ATN, no solo lo que reciben las provincias); no es la recaudación tributaria nacional total, que incluye impuestos no coparticipables.

Es un modelo deliberadamente simple: el impacto en cada provincia es el shock multiplicado por la masa y por su coeficiente. Una consecuencia directa es que, en porcentaje de lo que le corresponde por coeficiente, todas las provincias pierden exactamente lo mismo. En una primera versión mostré además el impacto como % de lo que cada provincia efectivamente cobró en 2025, y aparecían diferencias que presenté como resultado. Las saqué: no reflejan exposición distinta, solo que lo cobrado no sigue exactamente los coeficientes legales. El Núcleo 5 muestra por qué: sin la compensación del Consenso Fiscal, cada jurisdicción recibe su coeficiente legal con diferencias menores a 0,2 puntos. Lo que sí diferencia la gravedad del golpe entre provincias es cuánto depende cada una de la coparticipación, que es el Núcleo 4.

El simulador usa únicamente los coeficientes de Ley 23.548: no incluye la compensación del Consenso Fiscal (Ley 27.429) porque es un monto fijado en pesos, no una proporción de la recaudación corriente. Tampoco modela los adelantos de coparticipación (como el Decreto 219/2026), que son anticipos a cuenta y no cambian el coeficiente de nadie. Y el shock se aplica de forma proporcional a toda la masa coparticipable, sin distinguir por impuesto (IVA, Ganancias, etc.), aunque en la práctica una caída de recaudación puede pegarle distinto a cada uno.

La interfaz interactiva del notebook es un slider de `ipywidgets`, para que todo siga siendo reproducible desde los notebooks sin un servidor aparte. Para poder usarlo sin instalar nada armé además una página estática (`docs/simulador/index.html`, publicada con GitHub Pages) que reimplementa la misma fórmula en JavaScript. Usa la misma calibración que el indicador de sensibilidad del Núcleo 4 (masa coparticipable 2025 calibrada con la coparticipación que registra el archivo provincial, sin la compensación del Consenso Fiscal) y muestra el impacto en pesos y como % de la recaudación total de Córdoba de 2025. Sus constantes son una foto de los datos 2025 de este repositorio: si incorporo años nuevos hay que recalcularlas a mano. El GIF del README (`scripts/build_demo_gif.py`, fuera del pipeline de datos) usa la misma calibración.

Notebook: `notebooks/03_simulador_sensibilidad.ipynb`.

### Supuestos y limitaciones

Para tener un escenario de referencia usé una cifra pública de comienzos de 2026: la caída de recaudación del primer cuatrimestre que reportó IARAF ($5,1 billones de caída total, $1,4 billones menos de coparticipación).

La caída total está en el [informe de IARAF del 5 de mayo de 2026](https://www.iaraf.org/index.php/13-areas-de-estudio/area-fiscal/723-informe-economico-2026-05-05): −6,7% real interanual en el primer cuatrimestre, una merma de unos $5,1 billones. Los $1,4 billones de menor coparticipación no figuran en ese resumen; según la prensa están en el informe completo, que IARAF publica en Google Drive y no pude abrir. No es la única cifra que circuló: Ámbito publicó el mismo día una pérdida de casi $1,3 billones para las provincias, a partir de datos que difundió el diputado Guillermo Michel ([nota](https://www.ambito.com/economia/provincias-presion-ya-perdieron-13-billones-coparticipacion-lo-que-va-2026-n6274308)), y el propio IARAF estimó que las transferencias automáticas cayeron un 5,7% real en enero-abril ([informe del 30 de abril de 2026](https://www.iaraf.org/index.php/informes-economicos/area-fiscal/722-informe-economico-2026-04-30)). Mantengo $1,4 billones como escenario de referencia. Como el modelo es lineal, con $1,3 billones la variación implícita sería −5,9% y el impacto sobre Córdoba de unos $111.500 millones en vez de $120.100 millones.

No encontré una cifra oficial de masa coparticipable para ese período, así que la estimo en `scripts/calibracion_iaraf.py`: tomo la coparticipación nominal 2025 del Núcleo 1 sin la compensación del Consenso Fiscal, la divido por 3 (un cuatrimestre), la llevo a precios de enero-abril de 2026 con el IPC nacional (+21,5% contra el promedio de 2025) y la divido por la suma de los 24 coeficientes, 0,5876, para llegar a la masa total. Después calculo qué variación % reproduce exactamente los $1,4 billones: −6,3%.

El ajuste de precios lo agregué en una revisión posterior. Antes la masa quedaba en pesos promedio de 2025 contra un impacto medido en pesos de 2026, y la variación implícita salía en −7,7%, sobreestimada en esa misma proporción.

Eso es una calibración, no una validación. El impacto en pesos sobre cada provincia no depende de la masa estimada: son los $1,4 billones repartidos por coeficiente (para Córdoba, unos $120.100 millones en el cuatrimestre). La variación implícita sí depende de esa estimación.

No hay una serie de masa coparticipable 2026 contra la cual validarla, pero sí se puede contrastar con Córdoba: el archivo de Rentas del Núcleo 4 trae lo que la provincia cobró mes a mes hasta agosto de 2026. En `contrastar_con_cordoba` (`scripts/calibracion_iaraf.py`) comparo enero-abril de 2026 con enero-abril de 2025, cada mes llevado a precios del mismo mes de 2026 con el IPC, usando solo la parte de la coparticipación que sigue los coeficientes. Córdoba perdió un 7,3% real, unos $134.100 millones. El modelo estima 6,3% y $120.100 millones: acierta el orden de magnitud y subestima la pérdida en alrededor de 10%. Si todas las provincias hubieran perdido lo mismo que Córdoba, la pérdida total habría sido de unos $1,56 billones. No puedo separar qué explica la diferencia con los $1,4 billones: puede pesar el deflactor (IARAF publicó antes de conocerse el IPC de abril y supuso 2,5%), qué conceptos entran en cada cifra y cuándo registra Rentas cada transferencia. El escenario de −6,3% es, si algo, conservador. En una versión anterior presentaba como chequeo que la masa afectada era ~46,7% de la caída total, dentro del rango habitual de la parte coparticipable de la recaudación. No era un chequeo: ese porcentaje sale de $1,4 billones / 0,5876 / $5,1 billones y da igual con cualquier masa estimada. Solo muestra que las dos cifras de IARAF son coherentes entre sí.

---

## Núcleo 4 — Peso de la coparticipación en las cuentas de Córdoba

### Fuentes

- **Recaudación de Córdoba, 2015-2025**: recaudación administrada por la Dirección General de Rentas de Córdoba (probablemente republicada por la Dirección General de Estadística y Censos; no encontré una URL pública estable del archivo). Archivo: `data/raw/ingresos_cordoba/serie_recaudacion_provincial.xlsx`, hoja `Serie_Mensual`, mensual desde enero de 2015.
- Para control, la coparticipación de Córdoba de la serie RON del Núcleo 1, una fuente independiente. También reutiliza el simulador del Núcleo 3.

### Metodología

Todo el ratio sale de un solo archivo. Leo estas filas por su código: el **Total** (1, recursos de origen provincial + recursos de origen nacional), que llamo recaudación total; los **Recursos de Origen Provincial** (1.1), que son la recaudación propia; y la **coparticipación**, con la misma definición que el Núcleo 1, como suma de tres filas: Coparticipación Federal de Impuestos (1.2.1: Ley 23.548 + compensación y bono del Consenso Fiscal), Fondo para Obras de Infraestructura y Programas Sociales (1.2.3, Ley 27.429 punto I.c) y Financiamiento Educativo (1.2.5.1, Ley 26.075). El ratio de dependencia es (1.2.1 + 1.2.3 + 1.2.5.1) / 1.

Llegar a esa definición tuvo dos pasos. En la primera versión usé como numerador la coparticipación de la serie nacional (Núcleo 1) y como denominador el total de este archivo; después pasé a usar solo la fila 1.2.1 del archivo provincial. Las dos fuentes coincidían en 2015-2017, pero desde 2018 la nacional registraba entre 14% y 17% más, y durante un tiempo no supe por qué. La causa es el Consenso Fiscal: en 2018 eliminó la asignación específica de Ganancias y pasó esa plata a la Ley 23.548. Hacienda la informa como coparticipación; Córdoba la sigue anotando aparte, en la fila 1.2.3, que antes de 2018 registraba esa misma asignación. Sumando 1.2.3 y el Financiamiento Educativo (que Córdoba también anota aparte, en 1.2.5.1), las dos fuentes coinciden todos los años con diferencias menores al 1,6%, y menores al 0,1% desde 2023. La comparación queda como columna de control en el CSV (`coparticipacion_ron_pesos`, `diferencia_ron_vs_provincia`), como sección propia en el notebook y como test.

El ratio da lo mismo en pesos nominales o reales, porque el deflactor se cancela en la división. Para ver por qué se mueve, en cambio, hacen falta los niveles en pesos constantes (en pesos de 2025, la misma unidad que los gráficos del Núcleo 1, con el mismo IPC empalmado, `load_ipc_empalmado`; `real = nominal × (ipc_2025 / ipc_año)`) del total, de la recaudación propia y de la coparticipación. Entre 2015 y 2025 la coparticipación creció un 3,8% real y la recaudación propia un 6,5%, pero la recaudación propia cayó un 20% entre 2017 y 2020, no se recuperó hasta 2025 y ese año seguía 5,6% por debajo de 2017. La coparticipación también cayó entre 2017 y 2020 (−11%), pero se recuperó un 20% hasta 2022. Eso es lo que llevó el ratio de 52,0% (2015) a 57,6% (2023); en 2025 la recaudación propia se recuperó y el ratio bajó a 53,1%.

Para el indicador de sensibilidad reutilizo `scripts/simulator.py::simular_shock`. La masa coparticipable de referencia la calibro para que el coeficiente de Córdoba reproduzca la coparticipación que registra el archivo provincial en 2025, sin la compensación y el bono del Consenso Fiscal (filas 1.2.1.2 y 1.2.1.3: son montos fijos, no un porcentaje de la recaudación), en `base_calibrada_cordoba`. Después divido el impacto en pesos por la recaudación total de 2025. Así impacto y denominador salen de la misma fuente, y el resultado es, por construcción, el shock multiplicado por la parte proporcional del ratio de 2025 (52,4% de un ratio total de 53,1%): una caída del 10% en la recaudación coparticipable reduce la recaudación total de Córdoba en un 5,2%. Queda en pesos nominales de 2025 porque es un escenario puntual, no una serie.

**Comparación con las demás provincias** (`scripts/build_dependencia_provincias.py`). El archivo de Rentas existe solo para Córdoba, así que para compararla uso la ejecución presupuestaria provisoria de la Administración Pública No Financiera de cada jurisdicción (esquema ahorro-inversión-financiamiento, base caja), que publica la Dirección Nacional de Coordinación Fiscal con las Provincias: `data/raw/ejecucion_presupuestaria_provincial/serie_aif-apnf-2025.xlsx` (<https://www.argentina.gob.ar/sites/default/files/serie_aif-apnf-2025.xlsx>), 2005-2025, mismo formato para las 24. Como control, su fila de Ley 23.548 más Financiamiento Educativo coincide al peso con la serie de transferencias de Hacienda del Núcleo 1 (sin la compensación del Consenso Fiscal), en las 24 jurisdicciones y en todos los años 2018-2025; hay un test.

El indicador principal es la dependencia de las transferencias nacionales: recursos tributarios de origen nacional (coparticipación y demás regímenes automáticos) más transferencias corrientes y de capital recibidas, sobre los ingresos totales **sin las contribuciones a la seguridad social**. Las saco del denominador porque solo las registran las provincias que conservan su caja de jubilaciones (Córdoba entre ellas, 13,7% de sus ingresos en 2025): con ellas adentro, esas provincias parecerían menos dependientes solo por tener caja propia. Calculo además los recursos de origen nacional sobre ingresos corrientes (lo más parecido al ratio de Rentas, pero sobre el presupuesto completo) y los recursos tributarios propios sobre el mismo denominador. El conjunto de las jurisdicciones es un cociente de sumas (ponderado por tamaño, así que lo dominan Buenos Aires y CABA); por eso muestro también la mediana y la mitad central.

Resultado: en 2025 las transferencias nacionales fueron el 52,4% de los ingresos de Córdoba, la sexta menos dependiente de 23 jurisdicciones con datos (detrás de Neuquén, con 38% de sus ingresos en regalías, CABA, Chubut, Santa Cruz y Buenos Aires), contra un conjunto de 53,7% y una mediana de 66%. En 2005 eran el 66,9% (puesto 11 de 24). Casi toda la dependencia de Córdoba es automática: en 2025, 49,1 puntos son recursos de origen nacional y 3,4 puntos transferencias corrientes y de capital, que en su mayoría son no automáticas (programas, convenios, obras, ATN). El esquema no abre esas transferencias por tipo, así que no puedo separar las pocas que siguen alguna regla fija. En el conjunto, esas transferencias pasaron de 7,5% de los ingresos en 2023 a 2,2% en 2024. Contra ingresos corrientes, los recursos de origen nacional son el 42,9% del presupuesto de Córdoba, bastante menos que el 53,1% de su recaudación total.

Scripts: `scripts/build_dependencia_fiscal.py` y `scripts/build_dependencia_provincias.py`. Notebook: `notebooks/04_dependencia_fiscal_cordoba.ipynb`.

### Supuestos y limitaciones

El denominador es la recaudación total, no los ingresos corrientes del presupuesto provincial. Lo propio es lo que administra Rentas: tributos y algunos recursos no tributarios, como multas. Según la nota al pie del archivo, excluye lo que recaudan otros organismos públicos provinciales, por ejemplo el Fondo para el Desarrollo Energético Provincial que recauda EPEC. Tampoco incluye los aportes y contribuciones a la Caja de Jubilaciones ni las transferencias no automáticas de Nación, que sí forman parte de los ingresos corrientes. En una versión anterior llamaba a este total "ingresos corrientes" y era incorrecto: contra los ingresos corrientes, los recursos de origen nacional son el 42,9% (2025), según la ejecución presupuestaria.

La comparación entre provincias tiene sus propias limitaciones. Son ejecuciones provisorias, base caja. La Pampa no tiene datos de 2025 (la fuente trae ceros) y queda afuera de ese año, sin completar; para La Pampa y San Luis la fuente aclara que los datos son estimaciones de la DNCFP, sin decir de qué años. Las transferencias recibidas no vienen abiertas por origen: casi todas son de Nación, pero puede haber otras. Y la dependencia baja no siempre significa más recaudación tributaria propia: en Neuquén la explican las regalías.

El encabezado de las hojas dice "Millones de pesos corrientes", pero los valores están en pesos corrientes. Lo verifiqué con la coparticipación: coincide con la serie de Hacienda del Núcleo 1, expresada en pesos, con diferencias menores al 1,6% todos los años.

La columna de diciembre de 2023 en `Serie_Mensual` está guardada como texto ("dic-23") en vez de fecha, a diferencia de las demás; el script la parsea aparte.

Y, como en el Núcleo 3, el indicador de sensibilidad es una simplificación de primera ronda: no modela respuestas de política provincial (ajuste de gasto, recaudación propia adicional, endeudamiento) ante una caída de ingresos.

---

## Núcleo 5 — Las 24 jurisdicciones comparadas

Usa la serie del Núcleo 1 (con el detalle por concepto de `load_ron_por_concepto`), los coeficientes del Núcleo 2, la población de cada año estimada entre censos (`scripts/poblacion.py`, ver Núcleo 1) y la población por jurisdicción del Censo 2022 de INDEC, resultados definitivos (`data/raw/poblacion/c2022_tp_est_c1.xlsx`, descargado de <https://www.indec.gob.ar/ftp/cuadros/poblacion/c2022_tp_est_c1.xlsx>). El cuadro trae dos subtotales de Buenos Aires sin código de jurisdicción (24 partidos del GBA y resto) que se descartan; el script controla que las 24 jurisdicciones sumen el total del país, 45.892.285 personas.

### Metodología

Cuatro comparaciones entre las 23 provincias y CABA:

- **Crecimiento real por habitante 2004-2025**: coparticipación real 2025 / real 2004, dividida por el crecimiento de la población estimada de cada jurisdicción. Una versión anterior mostraba el crecimiento del monto real entre 2003 y 2025, que daba casi lo mismo para todas (23 de las 24 entre ×3,10 y ×3,20): con coeficientes fijos, el resultado era casi mecánico, y arrancaba en el piso de la crisis. Por habitante, el rango va de ×1,10 (Tierra del Fuego) a ×1,98 (CABA), y casi toda la diferencia la explica el crecimiento de la población (correlación de rangos −0,98), porque la Ley 23.548 no tiene ningún componente que siga a la población. El CSV conserva las dos medidas.
- **Participación en el reparto, año por año**: lo que recibió cada una sobre el total de las 24 (en montos nominales; el deflactor es común y se cancela), medido como diferencia en puntos porcentuales contra su propia participación de 2003 para poder mostrar en un mismo eje a Buenos Aires (más de 20%) y a Tierra del Fuego (poco más de 1%).
- **Participación 2025 contra el coeficiente legal** renormalizado entre las 24 (la misma base del Núcleo 2), con y sin la compensación del Consenso Fiscal.
- **Por habitante**: coparticipación 2022 dividida por la población del Censo 2022, llevada a pesos de 2025 con el mismo IPC del Núcleo 1 (`nominal_2022 × ipc_2025 / ipc_2022`), y un índice contra el promedio de las 24 ponderado por población (promedio = 1). El índice es igual a la participación de 2022 en el reparto dividida por la participación en la población; hay un test que lo controla.

Script: `scripts/build_comparativo_provincias.py`. Notebook: `notebooks/05_comparacion_provincias.ipynb`.

### Supuestos y limitaciones

La foto por habitante de cada jurisdicción contra el promedio es de 2022, el año del censo: para 2025 tendría que usar la población extrapolada, y no tengo en el repositorio proyecciones oficiales de población por provincia basadas en el Censo 2022. El crecimiento por habitante 2004-2025 sí usa la población estimada de 2025, con el supuesto de extrapolación del Núcleo 1; un error de un par de puntos en la población de 2025 no cambia el orden, porque las diferencias de crecimiento poblacional entre jurisdicciones van de 13% a 90%. El censo es del 18 de mayo de 2022 y la coparticipación es la suma del año, una diferencia de meses que no cambia el orden de las jurisdicciones. El resultado (cuanto menos población, más coparticipación por habitante) refleja el diseño de los coeficientes, que son fijos y no dependen de la población; no lo interpreto como una medida de necesidad ni de eficiencia del gasto.

Los movimientos de la participación los asocio a cambios de reglas conocidos (Fondo del Conurbano congelado hasta 2017, Decreto 194/2016 y Ley 27.606 para CABA, fallos de la Corte Suprema de noviembre de 2015 sobre la detracción del 15% para la ANSES). La serie muestra los movimientos y su momento coincide con esas normas, pero no reconstruyo cada norma por separado: es una lectura de los datos, no una descomposición contable.

Sin la compensación del Consenso Fiscal, 23 de las 24 jurisdicciones reciben su coeficiente legal con diferencias menores a 0,05 puntos. Santa Fe recibe 0,15 puntos más, y no identifiqué por qué. El 1,55% adicional que Nación transfiere a CABA por la cautelar de 2022 no aparece en la serie de Hacienda que uso, así que la participación de CABA desde 2023 lo deja afuera.

---

## Apéndice: fuentes evaluadas y descartadas para el Núcleo 1

Cuando el Núcleo 1 todavía estaba acotado a 2016-2025 (antes de conseguir la base de Ferreres/Norte y Sur), evalué y descarté estas fuentes para cubrir 2003-2015. Las series del Banco Mundial no se conservan en el repositorio; las dejo acá como registro, aunque ya no son relevantes para el alcance actual:

- **IPC INDEC "histórico" (`sh_ipc_12_16.xls`)**: pese al nombre, solo cubre abril-noviembre 2016 — no suma cobertura hacia atrás.
- **Series del Banco Mundial vía FRED (`DDOE01ARA086NWDB`, `DDOE02ARA086NWDB`)**: cubren 1960-2014 y 1960-2015. El tramo 2003-2013 es internamente coherente, pero 2014 y 2015 muestran el índice bajando respecto de 2013 (134,7 → 105,5 → 120,6), algo económicamente imposible dado que Argentina tuvo inflación alta y positiva esos años — parece un empalme mal hecho en el propio dataset del Banco Mundial, no un error mío al descargarlo, y coincide justo con el período de descrédito del IPC oficial.
- **Serie FRED `FPCPITOTLZGARG`** (inflación anual %, Banco Mundial): solo cubre 2018-2024, no aporta al hueco 2007-2015.
