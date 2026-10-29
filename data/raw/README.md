# data/raw — trazabilidad de fuentes

Esta carpeta tiene los datos crudos, tal como los conseguí. Nunca se editan a mano. Cada subcarpeta corresponde a una fuente y tiene su propio `_metadata.json` con el origen exacto de cada archivo.

## Fuentes

| Fuente | Carpeta | Núcleo(s) |
|---|---|---|
| Coparticipación / RON — Secretaría de Hacienda | `coparticipacion/` | 1, 3 |
| IPC — INDEC y Fundación Norte y Sur / Ferreres | `ipc/` | 1, 4 |
| PBG por provincia — CEPAL | `pbg/` | 2 |
| Coeficientes de coparticipación | `coeficientes/` | 2, 3 |
| Recaudación de Córdoba — Dirección General de Rentas | `ingresos_cordoba/` | 4 |
| Población por jurisdicción — INDEC, censos 2001, 2010 y 2022 | `poblacion/` | 1, 5 |
| PIB nacional — INDEC, cuentas nacionales | `pib_nacional/` | 1 |
| Derechos de exportación — Secretaría de Hacienda (vía datos.gob.ar) | `fiscal_nacional/` | 2 |
| Exportaciones por provincia y rubro — INDEC (vía datos.gob.ar) | `exportaciones/` | 2 |
| Ejecución presupuestaria provincial — DNCFP, Ministerio de Economía | `ejecucion_presupuestaria_provincial/` | 4 |

### Cómo los conseguí

Todos los archivos los descargué o los conseguí a mano y los versioné acá tal cual, así el proyecto se puede reproducir sin acceso a internet. Cada `_metadata.json` anota de dónde salió cada archivo y cuándo lo incorporé.

### Coparticipación federal / Recursos de Origen Nacional (RON)

- **Organismo**: Secretaría de Hacienda, Ministerio de Economía de la Nación.
- **URL de origen**: <https://www.argentina.gob.ar/economia/sechacienda/asuntosprovinciales/ron>
- **Archivo usado**: `coparticipacion/serie_ron_2003_2025.csv` — 2003 a 2025, un registro por provincia/año/concepto (14 conceptos distintos de RON, no solo coparticipación Ley 23.548). Qué conceptos uso exactamente para este núcleo está detallado en `docs/methodology.md`.
- **Contexto normativo**: distribución automática y diaria bajo el régimen de la Ley 23.548 (1988) y modificaciones posteriores (por ejemplo, la compensación por el Consenso Fiscal desde 2018). El archivo agrega esa distribución diaria a nivel anual.

### Índice de Precios al Consumidor (IPC)

- **2016-2025 — INDEC**: `ipc/serie_ipc_divisiones.csv` — Region="Nacional", Nivel General, cobertura mensual desde diciembre de 2016. El IPC oficial de Argentina no tiene cobertura confiable antes de esa fecha con las fuentes a las que pude acceder directamente de INDEC (el detalle está en `docs/methodology.md`, en la parte sobre la confiabilidad del IPC oficial en 2007-2015).
- **2003-2015 — Fundación Norte y Sur / Orlando Ferreres**: `ipc/ferreres_variaciones_usadas.csv`, con solo las 14 tasas de variación anual que usa el empalme, transcriptas de la hoja `IPC ` del archivo de la fuente (conseguido en forma directa, sin URL pública de origen verificada). El archivo completo es una compilación de series desde ~1810 y no lo redistribuyo acá. La uso para empalmar el IPC hacia atrás desde 2016: el tramo 2004-2006 sale de la tabla "GBA (INDEC)" (pre-intervención, confiable), y el tramo 2007-2016 de la tabla "GBA (estimaciones privadas)" (reemplaza al IPC oficial de esos años, bastante desacreditado por la intervención del INDEC). El método exacto, y una limitación que no pude resolver sobre una nota del archivo ("Ver metodología" sin hoja de metodología adjunta), están en `docs/methodology.md`.
- Con este empalme, el Núcleo 1 pasó de cubrir 2016-2025 a cubrir 2003-2025. No llega a 1990 porque no encontré ninguna fuente de montos nominales de coparticipación anterior a 2003 (ver la sección de RON arriba).

### Recaudación de Córdoba (Núcleo 4)

- **Organismo**: Dirección General de Rentas de la Provincia de Córdoba (archivo que ya tenía armado de antes).
- **Archivo usado**: `ingresos_cordoba/serie_recaudacion_provincial.xlsx` (nombre original: `Serie-recaudacion-provincial_Ene15-Ago26.xlsx`), hoja `Serie_Mensual`: recaudación mensual por concepto, enero 2015 a agosto 2026. Para el Núcleo 4 uso solo años calendario completos, 2015-2025, y tres filas: el total, los recursos de origen provincial y la coparticipación federal.
- **Limitación de alcance**: el total excluye lo recaudado por otros organismos públicos provinciales (por ejemplo, EPEC), según la nota al pie del archivo. El detalle, incluida la corrección de unidades (el archivo dice "millones de pesos" pero son pesos), está en `docs/methodology.md`.

### Población por jurisdicción (Núcleos 1 y 5)

- **Organismo**: INDEC, Censo Nacional de Población, Hogares y Viviendas 2022, resultados definitivos.
- **URL de origen**: <https://www.indec.gob.ar/ftp/cuadros/poblacion/c2022_tp_est_c1.xlsx> (listado en <https://www.indec.gob.ar/indec/web/Nivel4-Tema-2-41-165>).
- **Archivo usado**: `poblacion/c2022_tp_est_c1.xlsx`, hoja `Cuadro 1 ` (con el espacio final del original), columnas 2010 y 2022. Las 24 jurisdicciones suman el total del país, 45.892.285 personas; el script lo controla.
- **Censo 2001**: `poblacion/censos_2001_2010_cuadro8.csv`, transcripción de las columnas de población del Cuadro 8 del Tomo 1 de resultados definitivos del Censo 2010 (<https://www.indec.gob.ar/ftp/cuadros/poblacion/censo2010_tomo1.pdf>, página 64 del libro). El PDF pesa 12 MB y no lo versiono; su SHA-256 está en `_metadata.json`. La transcripción suma el total del país en 2001 y 2010, y su columna 2010 coincide con la del Censo 2022 en las 24 jurisdicciones (lo controla un test).

### PIB nacional (Núcleo 1)

- **Organismo**: INDEC, cuentas nacionales, año base 2004.
- **URL de origen**: <https://www.indec.gob.ar/ftp/cuadros/economia/sh_oferta_demanda_09_26.xls> (listado en <https://www.indec.gob.ar/indec/web/Nivel4-Tema-3-9-47>).
- **Archivo usado**: `pib_nacional/sh_oferta_demanda_09_26.xls`, hojas `cuadro 8` (precios corrientes) y `cuadro 1` (precios de 2004), fila "Producto Interno Bruto", columnas "Total" de cada año. Cubre 2004-2025; no tiene 2003.

### Ejecución presupuestaria provincial (Núcleo 4)

- **Organismo**: Dirección Nacional de Coordinación Fiscal con las Provincias, Ministerio de Economía de la Nación.
- **URL de origen**: <https://www.argentina.gob.ar/sites/default/files/serie_aif-apnf-2025.xlsx> (listado en <https://www.argentina.gob.ar/economia/sechacienda/coordinacion-fiscal-provincial/ejecucion-presupuestaria-provincial/ejecuciones>).
- **Archivo usado**: `ejecucion_presupuestaria_provincial/serie_aif-apnf-2025.xlsx`: esquema ahorro-inversión-financiamiento de la Administración Pública No Financiera, una hoja por jurisdicción, 2005-2025, en millones de pesos corrientes. La Pampa no tiene datos de 2025.

### Derechos de exportación y exportaciones por provincia (Núcleo 2)

- **Derechos de exportación**: serie anual de recursos tributarios por tributo de la Secretaría de Hacienda, descargada de la API de series de tiempo de datos.gob.ar (`fiscal_nacional/derechos_exportacion_anual.csv`, millones de pesos corrientes, 1997-2025).
- **Exportaciones por provincia y rubro**: INDEC (origen provincial de las exportaciones), misma API (`exportaciones/exportaciones_cordoba_y_total_por_rubro.csv`): total del país y Córdoba, por grandes rubros, 1993-2024.
- Las URL exactas de descarga, con los ids de cada serie, están en el `_metadata.json` de cada carpeta.

## Otros archivos en esta carpeta

`coparticipacion/serie_ron_2003_2025.xlsx` es el mismo contenido que el CSV, que es el que se usa. `ipc/serie_ipc_aperturas.csv` e `ipc/ipc_transicion_abr_nov_2016.xls` son descargas de INDEC que evalué y no usé; el motivo de cada una está en `ipc/_metadata.json`.
