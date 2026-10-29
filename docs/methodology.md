# Metodología

Estas son las notas técnicas del proyecto: de dónde sale cada dato, qué decisiones tomé al procesarlo y dónde el análisis tiene puntos flojos. El resumen de hallazgos y las instrucciones para correr todo están en el [README](../README.md) — acá va el detalle que sostiene cada número.

Va organizado en una sección por núcleo (fuentes, metodología, supuestos y limitaciones), más un apéndice al final con fuentes que evalué y descarté para el Núcleo 1.

## Cómo conseguí los datos

Todos los archivos de `data/raw/` los descargué o los conseguí a mano y los versioné tal cual, así el proyecto se reproduce sin acceso a internet. La trazabilidad de cada archivo (de dónde salió, qué alcance tiene, por qué lo usé o lo descarté) está en [`data/raw/README.md`](../data/raw/README.md).

---

## Núcleo 1 — Serie histórica de coparticipación (2003-2025)

### Fuentes

- **Coparticipación federal / Recursos de Origen Nacional (RON)**: Secretaría de Hacienda, Ministerio de Economía de la Nación. <https://www.argentina.gob.ar/economia/sechacienda/asuntosprovinciales/ron>. Archivo: `data/raw/coparticipacion/serie_ron_2003_2025.csv` (2003-2025).
- **IPC 2016-2025**: INDEC. <https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv>. Archivo: `data/raw/ipc/serie_ipc_divisiones.csv` (mensual, desde dic-2016).
- **IPC 2003-2015**: Fundación Norte y Sur / Orlando J. Ferreres, conseguida en forma directa (sin URL pública verificada). En el repositorio está solo lo que uso: las 14 tasas de variación anual del empalme, transcriptas de la hoja `IPC ` del archivo original, en `data/raw/ipc/ferreres_variaciones_usadas.csv`. El archivo completo es una compilación de series desde ~1810 y no lo redistribuyo. Es la compilación histórica de series económicas de Argentina que hizo Ferreres para la Fundación Norte y Sur (conocido por *"Dos siglos de Economía Argentina"*) — la uso como insumo de análisis, sin reclamar autoría sobre la compilación.

Incorporé estos datos el 20 de agosto de 2026 (con el rango original acotado a 2016-2025), y amplié a 2003-2025 el 12 de septiembre.

### Metodología

El archivo de RON desagrega lo transferido a cada provincia en unos 14 conceptos (coparticipación Ley 23.548, Financiamiento Educativo, IVA, Ganancias, Bienes Personales, combustibles líquidos, régimen simplificado, etc.). Definí "coparticipación" como la coparticipación Ley 23.548 **bruta**, más la compensación del Consenso Fiscal (Ley 27.429, desde 2018), más, hasta 2017, las asignaciones específicas de Ganancias. Las dos piezas que no son obvias:

- **Bruto o neto.** Hacienda informa la Ley 23.548 de dos maneras según el año: como monto bruto ("coparticipación federal de impuestos Ley 23.548", en 2003-2005 y 2011) o como monto neto de la parte que la Ley 26.075 afecta a educación ("neta Ley 26.075"), con esa parte en un concepto aparte ("financiamiento educativo Ley 26.075", en 2006-2010 y 2012-2025). En una primera versión traté el bruto y el neto como el mismo concepto. Era un error: el Financiamiento Educativo no se reparte con los coeficientes, pesa entre 5% y 33% de lo que recibe cada jurisdicción (en 2025: 5% en Tierra del Fuego, 13% en Córdoba, 24% en Buenos Aires, 33% en CABA), y cada cambio de forma metía un salto falso, como el "pico" de 2011. Ahora sumo el neto y el Financiamiento Educativo. Un test (`test_bruto_y_neto_mas_financiamiento_educativo_son_el_mismo_concepto`) verifica que con esa suma la participación de cada jurisdicción no salte al cambiar de forma (menos de 0,25 puntos por año en 2003-2015; con solo el neto, saltaba hasta 1,7 puntos).
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

También agregué una lectura en términos relativos: además del gráfico en niveles absolutos (donde Buenos Aires domina el gráfico solo por su tamaño), indexé cada provincia a su propio valor de 2003 (=100). Ahí las cuatro provincias de referencia terminan casi iguales (310-314 puntos en 2025): el salto de la serie responde a la dinámica agregada del régimen, no a que a Córdoba le haya ido mejor o peor que al resto. En el camino, Buenos Aires se queda atrás entre 2004 y 2017 por el Fondo del Conurbano congelado, y Mendoza en 2016-2018 por la detracción para la ANSES; el Núcleo 5 extiende esta comparación a las 24 jurisdicciones. Sin este gráfico, el de niveles absolutos por sí solo podría sugerir, incorrectamente, que a Buenos Aires "le va mejor" en el régimen, cuando en realidad solo es más grande en nivel.

Script: `scripts/process_coparticipacion.py`. Notebook: `notebooks/01_serie_historica.ipynb`.

---

## Núcleo 2 — Aporte vs. recibo por provincia

### Fuentes

- **Producto Bruto Geográfico (PBG) por provincia**: CEPAL, sobre metodología base de INDEC (año base 2004). Archivo: `data/raw/pbg/Jurisdiccion_52sectores.xlsx` (hoja `VABpb`), 2004-2024. No es la publicación directa de INDEC (que en su archivo público solo llega a 2017) — es una actualización de CEPAL, la más reciente que encontré. En rigor es el Valor Agregado Bruto a precios básicos, en millones de pesos a precios de 2004; en el proyecto lo llamo PBG por simplicidad.
- **Coeficientes de coparticipación (Ley 23.548)**: planilla "Índices de Distribución de la Coparticipación Federal de Impuestos y Regímenes Especiales de Distribución". El documento no indica qué organismo la emitió; menciona que el Banco de la Nación Argentina distribuye en base a notas instructivas de la Secretaría de Hacienda. Archivo: `data/raw/coeficientes/indices_copa_2018.pdf`, creado el 2 de febrero de 2018 según la metadata del archivo.

### Metodología

Trabajo con las 24 jurisdicciones en un solo corte (no serie temporal). "Aporta" es el % del PBG de cada provincia sobre el PBG total del país en 2024, el año más reciente disponible (dato preliminar en la fuente). "Recibe" es la porción de cada provincia en lo que se reparte **entre provincias**: su coeficiente de Ley 23.548 (con el ajuste de CABA que explico abajo) dividido por la suma de los 24 coeficientes. La métrica es la diferencia en puntos porcentuales (recibe − aporta): positivo significa que la provincia recibe una porción del reparto mayor que su peso económico, negativo lo contrario.

Script: `scripts/build_coefficients_comparison.py`. Notebook: `notebooks/02_aporte_vs_recibo.ipynb`.

### Supuestos y limitaciones

El documento de coeficientes es de febrero de 2018, no la versión más actual: el valor de CABA ahí (3,75%) corresponde al Decreto 194/2016. Lo reemplacé por 1,4%, el coeficiente del régimen automático vigente desde la Ley 27.606 (2020); los otros 23 coeficientes no los toqué, porque son la tabla de la Ley 23.548 de 1988 y no cambiaron. Hay un detalle más: en diciembre de 2022 la Corte Suprema dictó una cautelar que obliga a Nación a transferirle a CABA un 1,55% adicional (2,95% en total), y en 2025 Nación y la Ciudad acordaron cómo cumplirla. Ese 1,55% se paga por fuera del régimen automático, así que mantengo el 1,4% para ser coherente con la serie de transferencias del Núcleo 1, y en el notebook muestro cómo cambia el resultado con 2,95% (la brecha de CABA pasa de −17,5 a −15,0 pp; la de Córdoba, de +0,01 a −0,2 pp). Tampoco modelé la excepción de Córdoba, Santa Fe y San Luis a la detracción del 15% para ANSES (es un descuento sobre la masa antes del reparto, no un coeficiente distinto).

Los 24 coeficientes suman ~0,59, no 1: el resto es lo que retienen Nación y el Fondo ATN. Por eso los renormalizo antes de compararlos con el PBG, que suma 100% entre provincias. En una primera versión los comparé sin renormalizar y el resultado era engañoso: como el coeficiente crudo es una fracción de un total más grande, todas las provincias grandes quedaban con brechas negativas por el solo hecho de ser grandes (Córdoba aparecía con −3,5 pp, cuando su porción del reparto, 8,58%, es prácticamente igual a su peso en el PBG, 8,56%). Renormalizado, el ranking mide cómo se reparte entre provincias, que es la pregunta del núcleo; cuánto se queda Nación es otra pregunta.

El PBG de la fuente está a precios constantes de 2004, así que la participación de cada provincia en 2024 está calculada con los precios relativos de 2004. En provincias donde el precio de lo que producen cambió mucho respecto del resto (las petroleras, por ejemplo), la participación a precios corrientes podría ser distinta. La fuente no trae una serie a precios corrientes, así que no lo puedo cuantificar.

El ranking usa el coeficiente legal, no lo que cada jurisdicción efectivamente cobra. El Núcleo 5 muestra que la diferencia entre las dos cosas es casi toda la compensación del Consenso Fiscal; con la participación efectiva de 2025, la brecha de Buenos Aires baja de −10,6 a −9,1 puntos, la de Córdoba pasa de +0,01 a −0,3 y el resto se mueve menos de 0,15 puntos. El notebook muestra las dos versiones.

El PBG como proxy del aporte tributario tiene un problema conocido: mide dónde se *genera* la actividad económica, no dónde se *paga* el impuesto. Las empresas grandes con operaciones en todo el país suelen tener domicilio fiscal en CABA, así que en las estadísticas de recaudación por jurisdicción buena parte de lo generado en otras provincias figura como pagado en CABA. Si usara esa recaudación en vez del PBG, CABA aparecería aportando todavía más y provincias productivas como Córdoba, menos. El PBG está más cerca de dónde se genera la actividad, pero no es una medición directa de lo que tributa cada provincia.

---

## Núcleo 3 — Simulador de sensibilidad

No tiene fuentes propias: reutiliza los coeficientes de coparticipación del Núcleo 2 (`scripts/coeficientes_ley23548.py`) y, para calibrar el escenario de referencia, la coparticipación nominal 2025 del Núcleo 1 sin la compensación del Consenso Fiscal.

### Metodología

El corazón es `simular_shock(variacion_pct_recaudacion, recaudacion_base, coeficientes_por_provincia)`, en `scripts/simulator.py`, con 9 tests automáticos en `scripts/test_simulator.py` (`pytest scripts/test_simulator.py`). `recaudacion_base` es la masa coparticipable TOTAL de referencia (incluye lo que retiene Nación y el Fondo ATN, no solo lo que reciben las provincias); no es la recaudación tributaria nacional total, que incluye impuestos no coparticipables.

Es un modelo deliberadamente simple: el impacto en cada provincia es el shock multiplicado por la masa y por su coeficiente. Una consecuencia directa es que, en porcentaje de lo que le corresponde por coeficiente, todas las provincias pierden exactamente lo mismo. En una primera versión mostré además el impacto como % de lo que cada provincia efectivamente cobró en 2025, y aparecían diferencias que presenté como resultado. Las saqué: no reflejan exposición distinta, solo que lo cobrado no sigue exactamente los coeficientes legales. El Núcleo 5 muestra por qué: sin la compensación del Consenso Fiscal, cada jurisdicción recibe su coeficiente legal con diferencias menores a 0,2 puntos. Lo que sí diferencia la gravedad del golpe entre provincias es cuánto depende cada una de la coparticipación, que es el Núcleo 4.

El simulador usa únicamente los coeficientes de Ley 23.548: no incluye la compensación del Consenso Fiscal (Ley 27.429) porque es un monto fijado en pesos, no una proporción de la recaudación corriente. Tampoco modela los adelantos de coparticipación (como el Decreto 219/2026), que son anticipos a cuenta y no cambian el coeficiente de nadie. Y el shock se aplica de forma proporcional a toda la masa coparticipable, sin distinguir por impuesto (IVA, Ganancias, etc.), aunque en la práctica una caída de recaudación puede pegarle distinto a cada uno.

La interfaz interactiva del notebook es un slider de `ipywidgets`, para que todo siga siendo reproducible desde los notebooks sin un servidor aparte. Para poder usarlo sin instalar nada armé además una página estática (`docs/simulador/index.html`, publicada con GitHub Pages) que reimplementa la misma fórmula en JavaScript. Usa la misma calibración que el indicador de sensibilidad del Núcleo 4 (masa coparticipable 2025 calibrada con la coparticipación que registra el archivo provincial, sin la compensación del Consenso Fiscal) y muestra el impacto en pesos y como % de los ingresos totales de Córdoba de 2025. Sus constantes son una foto de los datos 2025 de este repositorio: si incorporo años nuevos hay que recalcularlas a mano. El GIF del README (`scripts/build_demo_gif.py`, fuera del pipeline de datos) usa la misma calibración.

Notebook: `notebooks/03_simulador_sensibilidad.ipynb`.

### Supuestos y limitaciones

Para tener un escenario de referencia usé una cifra pública de comienzos de 2026: la caída de recaudación del primer cuatrimestre que reportó IARAF ($5,1 billones de caída total, $1,4 billones menos de coparticipación).

La caída total está en el [informe de IARAF del 5 de mayo de 2026](https://www.iaraf.org/index.php/13-areas-de-estudio/area-fiscal/723-informe-economico-2026-05-05): −6,7% real interanual en el primer cuatrimestre, una merma de unos $5,1 billones. Los $1,4 billones de menor coparticipación no figuran en ese resumen; según la prensa están en el informe completo, que IARAF publica en Google Drive y no pude abrir. No es la única cifra que circuló: Ámbito publicó el mismo día una pérdida de casi $1,3 billones para las provincias, a partir de datos que difundió el diputado Guillermo Michel ([nota](https://www.ambito.com/economia/provincias-presion-ya-perdieron-13-billones-coparticipacion-lo-que-va-2026-n6274308)), y el propio IARAF estimó que las transferencias automáticas cayeron un 5,7% real en enero-abril ([informe del 30 de abril de 2026](https://www.iaraf.org/index.php/informes-economicos/area-fiscal/722-informe-economico-2026-04-30)). Mantengo $1,4 billones como escenario de referencia. Como el modelo es lineal, con $1,3 billones la variación implícita sería −5,9% y el impacto sobre Córdoba de unos $111.500 millones en vez de $120.100 millones.

No encontré una cifra oficial de masa coparticipable para ese período, así que la estimo en `scripts/calibracion_iaraf.py`: tomo la coparticipación nominal 2025 del Núcleo 1 sin la compensación del Consenso Fiscal, la divido por 3 (un cuatrimestre), la llevo a precios de enero-abril de 2026 con el IPC nacional (+21,5% contra el promedio de 2025) y la divido por la suma de los 24 coeficientes, 0,5876, para llegar a la masa total. Después calculo qué variación % reproduce exactamente los $1,4 billones: −6,3%.

El ajuste de precios lo agregué en una revisión posterior. Antes la masa quedaba en pesos promedio de 2025 contra un impacto medido en pesos de 2026, y la variación implícita salía en −7,7%, sobreestimada en esa misma proporción.

Eso es una calibración, no una validación. El impacto en pesos sobre cada provincia no depende de la masa estimada: son los $1,4 billones repartidos por coeficiente (para Córdoba, unos $120.100 millones en el cuatrimestre). La variación implícita sí depende de esa estimación, y no tengo una serie independiente para contrastarla. En una versión anterior presentaba como chequeo que la masa afectada era ~46,7% de la caída total, dentro del rango habitual de la parte coparticipable de la recaudación. No era un chequeo: ese porcentaje sale de $1,4 billones / 0,5876 / $5,1 billones y da igual con cualquier masa estimada. Solo muestra que las dos cifras de IARAF son coherentes entre sí.

---

## Núcleo 4 — Peso de la coparticipación en las cuentas de Córdoba

### Fuentes

- **Recaudación de Córdoba, 2015-2025**: recaudación administrada por la Dirección General de Rentas de Córdoba (probablemente republicada por la Dirección General de Estadística y Censos; no encontré una URL pública estable del archivo). Archivo: `data/raw/ingresos_cordoba/serie_recaudacion_provincial.xlsx`, hoja `Serie_Mensual`, mensual desde enero de 2015.
- Para control, la coparticipación de Córdoba de la serie RON del Núcleo 1, una fuente independiente. También reutiliza el simulador del Núcleo 3.

### Metodología

Todo el ratio sale de un solo archivo. Leo estas filas por su código: el **Total** (1, recursos de origen provincial + recursos de origen nacional), que uso como proxy de ingresos corrientes totales; los **Recursos de Origen Provincial** (1.1), que son la recaudación propia; y la **coparticipación**, con la misma definición que el Núcleo 1, como suma de tres filas: Coparticipación Federal de Impuestos (1.2.1: Ley 23.548 + compensación y bono del Consenso Fiscal), Fondo para Obras de Infraestructura y Programas Sociales (1.2.3, Ley 27.429 punto I.c) y Financiamiento Educativo (1.2.5.1, Ley 26.075). El ratio de dependencia es (1.2.1 + 1.2.3 + 1.2.5.1) / 1.

Llegar a esa definición tuvo dos pasos. En la primera versión usé como numerador la coparticipación de la serie nacional (Núcleo 1) y como denominador el total de este archivo; después pasé a usar solo la fila 1.2.1 del archivo provincial. Las dos fuentes coincidían en 2015-2017, pero desde 2018 la nacional registraba entre 14% y 17% más, y durante un tiempo no supe por qué. La causa es el Consenso Fiscal: en 2018 eliminó la asignación específica de Ganancias y pasó esa plata a la Ley 23.548. Hacienda la informa como coparticipación; Córdoba la sigue anotando aparte, en la fila 1.2.3, que antes de 2018 registraba esa misma asignación. Sumando 1.2.3 y el Financiamiento Educativo (que Córdoba también anota aparte, en 1.2.5.1), las dos fuentes coinciden todos los años con diferencias menores al 1,6%, y menores al 0,1% desde 2023. La comparación queda como columna de control en el CSV (`coparticipacion_ron_pesos`, `diferencia_ron_vs_provincia`), como sección propia en el notebook y como test.

El ratio da lo mismo en pesos nominales o reales, porque el deflactor se cancela en la división. Para ver por qué se mueve, en cambio, hacen falta los niveles en pesos constantes (base 2016, mismo IPC empalmado que el Núcleo 1, `load_ipc_empalmado`; `real = nominal × (ipc_2016 / ipc_año)`) del total, de la recaudación propia y de la coparticipación. Entre 2015 y 2025 la coparticipación creció un 3,8% real y la recaudación propia un 6,5%, pero la recaudación propia cayó un 20% entre 2017 y 2020, no se recuperó hasta 2025 y ese año seguía 5,6% por debajo de 2017. La coparticipación también cayó entre 2017 y 2020 (−11%), pero se recuperó un 20% hasta 2022. Eso es lo que llevó el ratio de 52,0% (2015) a 57,6% (2023); en 2025 la recaudación propia se recuperó y el ratio bajó a 53,1%.

Para el indicador de sensibilidad reutilizo `scripts/simulator.py::simular_shock`. La masa coparticipable de referencia la calibro para que el coeficiente de Córdoba reproduzca la coparticipación que registra el archivo provincial en 2025, sin la compensación y el bono del Consenso Fiscal (filas 1.2.1.2 y 1.2.1.3: son montos fijos, no un porcentaje de la recaudación), en `base_calibrada_cordoba`. Después divido el impacto en pesos por los ingresos totales de 2025. Así impacto y denominador salen de la misma fuente, y el resultado es, por construcción, el shock multiplicado por la parte proporcional del ratio de 2025 (52,4% de un ratio total de 53,1%): una caída del 10% en la recaudación coparticipable reduce los ingresos totales de Córdoba en un 5,2%. Queda en pesos nominales de 2025 porque es un escenario puntual, no una serie.

Script: `scripts/build_dependencia_fiscal.py`. Notebook: `notebooks/04_dependencia_fiscal_cordoba.ipynb`.

### Supuestos y limitaciones

La nota al pie del archivo aclara que el Total excluye lo recaudado por otros organismos públicos provinciales, por ejemplo el Fondo para el Desarrollo Energético Provincial que recauda EPEC. No es el ingreso corriente total del sector público provincial en sentido estricto de ejecución presupuestaria, sino la mejor proxy que tengo; con esa recaudación incluida, el ratio sería algo menor.

El encabezado de las hojas dice "Millones de pesos corrientes", pero los valores están en pesos corrientes. Lo verifiqué con la coparticipación: coincide con la serie de Hacienda del Núcleo 1, expresada en pesos, con diferencias menores al 1,6% todos los años.

La columna de diciembre de 2023 en `Serie_Mensual` está guardada como texto ("dic-23") en vez de fecha, a diferencia de las demás; el script la parsea aparte.

Y, como en el Núcleo 3, el indicador de sensibilidad es una simplificación de primera ronda: no modela respuestas de política provincial (ajuste de gasto, recaudación propia adicional, endeudamiento) ante una caída de ingresos.

---

## Núcleo 5 — Las 24 jurisdicciones comparadas

Usa la serie del Núcleo 1 (con el detalle por concepto de `load_ron_por_concepto`), los coeficientes del Núcleo 2 y una fuente propia: la población por jurisdicción del Censo 2022 de INDEC, resultados definitivos (`data/raw/poblacion/c2022_tp_est_c1.xlsx`, descargado de <https://www.indec.gob.ar/ftp/cuadros/poblacion/c2022_tp_est_c1.xlsx>). El cuadro trae dos subtotales de Buenos Aires sin código de jurisdicción (24 partidos del GBA y resto) que se descartan; el script controla que las 24 jurisdicciones sumen el total del país, 45.892.285 personas.

### Metodología

Cuatro comparaciones entre las 23 provincias y CABA:

- **Crecimiento real 2003-2025**: coparticipación real 2025 / real 2003, por jurisdicción.
- **Participación en el reparto, año por año**: lo que recibió cada una sobre el total de las 24 (en montos nominales; el deflactor es común y se cancela), medido como diferencia en puntos porcentuales contra su propia participación de 2003 para poder mostrar en un mismo eje a Buenos Aires (más de 20%) y a Tierra del Fuego (poco más de 1%).
- **Participación 2025 contra el coeficiente legal** renormalizado entre las 24 (la misma base del Núcleo 2), con y sin la compensación del Consenso Fiscal.
- **Por habitante**: coparticipación 2022 dividida por la población del Censo 2022, llevada a pesos de 2025 con el mismo IPC del Núcleo 1 (`nominal_2022 × ipc_2025 / ipc_2022`), y un índice contra el promedio de las 24 ponderado por población (promedio = 1). El índice es igual a la participación de 2022 en el reparto dividida por la participación en la población; hay un test que lo controla.

Script: `scripts/build_comparativo_provincias.py`. Notebook: `notebooks/05_comparacion_provincias.ipynb`.

### Supuestos y limitaciones

La comparación por habitante es solo de 2022. Usé la coparticipación de ese año y no la de 2025 porque dividir montos de 2025 por la población de 2022 mezclaría años, y no tengo en el repositorio proyecciones oficiales de población por provincia basadas en el Censo 2022. El censo es del 18 de mayo de 2022 y la coparticipación es la suma del año, una diferencia de meses que no cambia el orden de las jurisdicciones. El resultado (cuanto menos población, más coparticipación por habitante) refleja el diseño de los coeficientes, que son fijos y no dependen de la población; no lo interpreto como una medida de necesidad ni de eficiencia del gasto.

Los movimientos de la participación los asocio a cambios de reglas conocidos (Fondo del Conurbano congelado hasta 2017, Decreto 194/2016 y Ley 27.606 para CABA, fallos de la Corte Suprema de noviembre de 2015 sobre la detracción del 15% para la ANSES). La serie muestra los movimientos y su momento coincide con esas normas, pero no reconstruyo cada norma por separado: es una lectura de los datos, no una descomposición contable.

Sin la compensación del Consenso Fiscal, 23 de las 24 jurisdicciones reciben su coeficiente legal con diferencias menores a 0,05 puntos. Santa Fe recibe 0,15 puntos más, y no identifiqué por qué. El 1,55% adicional que Nación transfiere a CABA por la cautelar de 2022 no aparece en la serie de Hacienda que uso, así que la participación de CABA desde 2023 lo deja afuera.

---

## Apéndice: fuentes evaluadas y descartadas para el Núcleo 1

Cuando el Núcleo 1 todavía estaba acotado a 2016-2025 (antes de conseguir la base de Ferreres/Norte y Sur), evalué y descarté estas fuentes para cubrir 2003-2015. Las series del Banco Mundial no se conservan en el repositorio; las dejo acá como registro, aunque ya no son relevantes para el alcance actual:

- **IPC INDEC "histórico" (`sh_ipc_12_16.xls`)**: pese al nombre, solo cubre abril-noviembre 2016 — no suma cobertura hacia atrás.
- **Series del Banco Mundial vía FRED (`DDOE01ARA086NWDB`, `DDOE02ARA086NWDB`)**: cubren 1960-2014 y 1960-2015. El tramo 2003-2013 es internamente coherente, pero 2014 y 2015 muestran el índice bajando respecto de 2013 (134,7 → 105,5 → 120,6), algo económicamente imposible dado que Argentina tuvo inflación alta y positiva esos años — parece un empalme mal hecho en el propio dataset del Banco Mundial, no un error mío al descargarlo, y coincide justo con el período de descrédito del IPC oficial.
- **Serie FRED `FPCPITOTLZGARG`** (inflación anual %, Banco Mundial): solo cubre 2018-2024, no aporta al hueco 2007-2015.
