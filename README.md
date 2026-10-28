# Coparticipación federal: el caso de Córdoba

[![CI](https://github.com/llorenzomagnano-sys/analisis-de-la-coparticipacion-federal-con-foco-en-cordoba/actions/workflows/ci.yml/badge.svg)](https://github.com/llorenzomagnano-sys/analisis-de-la-coparticipacion-federal-con-foco-en-cordoba/actions/workflows/ci.yml)

Análisis de datos del régimen de coparticipación federal de impuestos en Argentina, con foco en la provincia de Córdoba.

## Sobre este proyecto

La coparticipación federal es uno de esos temas que aparecen todo el tiempo en la agenda económica argentina — un gobernador reclamando por su provincia, un cambio de coeficientes generando discusión — pero que casi nunca se explican con números concretos y trazables. Armé este repositorio para entender mejor cómo funciona el reparto de la Ley 23.548 en la práctica, tomando a Córdoba como caso de estudio en vez de quedarme en generalidades sobre todo el país.

Lo organicé en cuatro preguntas que se van encadenando: cómo evolucionó en el tiempo la coparticipación real que recibe Córdoba, si la provincia recibe en proporción a lo que aporta, qué tan sensible es ese reparto a un shock de recaudación, y qué tan dependiente es el presupuesto provincial de esa plata. Una quinta parte pone a Córdoba en contexto y compara a las 24 jurisdicciones entre sí. De dónde sale cada dato, qué supuestos tomé y dónde flaquean queda documentado a la vista en vez de escondido en un anexo — es la parte del trabajo que más tiempo me llevó.

## Principales hallazgos

- **Serie histórica (2003-2025)**: la coparticipación real recibida por Córdoba (pesos constantes de 2016) pasó de $15.579 millones en 2003 a un máximo de $55.107 millones en 2022, y cerró 2025 en $48.221 millones, 3,1 veces el nivel de 2003. En términos relativos (indexado a 2003=100), Córdoba terminó prácticamente igual que Buenos Aires, Santa Fe y Mendoza (entre 310 y 314 puntos en 2025): el salto responde a la dinámica agregada del régimen, no a algo particular de cada provincia.
- **Aporte vs. recibo por provincia**: comparando la porción de cada provincia en lo que se reparte entre provincias con su peso en el PBG, Córdoba queda prácticamente empatada: recibe el 8,58% del reparto y representa el 8,56% del PBG. Las que quedan claramente por debajo son CABA (−17,5 pp), Buenos Aires (−10,6 pp) y Neuquén (−2,7 pp); las que más reciben en relación a su PBG, Chaco, Formosa y Tucumán (cerca de +3 pp cada una).
- **Simulador de sensibilidad**: calibrado con la caída de recaudación de comienzos de 2026 que dio a conocer IARAF, una baja de ~7,7% en la recaudación nacional coparticipable le cuesta a Córdoba unos $120.100 millones en un cuatrimestre. Como el reparto es proporcional, todas las provincias pierden el mismo porcentaje de lo que les corresponde; lo que cambia la gravedad del golpe es cuánto depende cada una de la coparticipación (Núcleo 4).
- **Dependencia fiscal de Córdoba (2015-2025)**: la coparticipación pasó de explicar el 52,0% de los ingresos de Córdoba en 2015 a un máximo de 57,6% en 2023, y bajó a 53,1% en 2025. En pesos constantes, la suba se explica sobre todo por la recaudación propia, que cayó un 20% entre 2017 y 2020 y se mantuvo cerca de ese piso hasta 2024, mientras la coparticipación se recuperaba. Con la dependencia de 2025, una caída del 10% en la recaudación nacional coparticipable reduce los ingresos totales de la provincia en un 5,2%.
- **Las 24 jurisdicciones comparadas**: entre 2003 y 2025, 22 de las 24 multiplicaron su coparticipación real entre 3,10 y 3,20 veces. Córdoba quedó última por poco (x3,10) y CABA se despegó (x3,57). Los movimientos grandes del reparto vienen de cambios de reglas y no de la economía de cada provincia: el Fondo del Conurbano congelado hasta 2017 le hizo perder a Buenos Aires 5 puntos del reparto, que recuperó con el Consenso Fiscal, y CABA pasó de 2% a más de 5% del reparto entre 2016 y 2020. Sin la compensación del Consenso Fiscal, cada jurisdicción recibe hoy prácticamente su coeficiente legal. Esa compensación va en un 56% a Buenos Aires, y por eso Córdoba recibe 0,29 puntos menos que su coeficiente: unos $157.100 millones en 2025, si se hubiera repartido según los coeficientes.

## Núcleos de análisis

| Núcleo | Descripción | Notebook |
|---|---|---|
| 1 | Serie histórica de coparticipación (2003-2025) | [`01_serie_historica.ipynb`](notebooks/01_serie_historica.ipynb) |
| 2 | Aporte vs. recibo por provincia | [`02_aporte_vs_recibo.ipynb`](notebooks/02_aporte_vs_recibo.ipynb) |
| 3 | Simulador de sensibilidad | [`03_simulador_sensibilidad.ipynb`](notebooks/03_simulador_sensibilidad.ipynb) |
| 4 | Peso de la coparticipación en las cuentas de Córdoba | [`04_dependencia_fiscal_cordoba.ipynb`](notebooks/04_dependencia_fiscal_cordoba.ipynb) |
| 5 | Las 24 jurisdicciones comparadas | [`05_comparacion_provincias.ipynb`](notebooks/05_comparacion_provincias.ipynb) |

La metodología completa — fuentes, supuestos y limitaciones de cada núcleo — está en [`docs/methodology.md`](docs/methodology.md).

### Núcleo 1 — Serie histórica de coparticipación

![Coparticipación real recibida por Córdoba, 2003-2025](output/figures/cordoba_evolucion_real_2003_2025.png)

En niveles absolutos Buenos Aires tapa todo por su tamaño, así que agregué también la misma serie indexada a 2003=100:

![Coparticipación real por provincia, indexada a 2003=100](output/figures/comparativo_provincias_indexado_2003_2025.png)

### Núcleo 2 — Aporte vs. recibo por provincia

![Coparticipación recibida vs. PBG aportado, por provincia](output/figures/aporte_vs_recibo_ranking.png)

### Núcleo 3 — Simulador de sensibilidad

Impacto en pesos del escenario de comienzos de 2026. En porcentaje, todas las provincias pierden lo mismo, porque el reparto es proporcional al coeficiente:

![Impacto de la caída de recaudación del primer cuatrimestre de 2026, por provincia](output/figures/simulador_impacto_1cuatrimestre2026.png)

Demo del simulador recorriendo distintos escenarios de shock, con el impacto como % de los ingresos totales de Córdoba (generada con `scripts/build_demo_gif.py`):

![Demo del simulador mostrando el impacto como % de los ingresos totales de Córdoba](output/figures/simulador_interactivo_demo.gif)

**[Probar el simulador en el navegador →](https://llorenzomagnano-sys.github.io/analisis-de-la-coparticipacion-federal-con-foco-en-cordoba/simulador/)**: misma fórmula de `simular_shock`, reimplementada en JavaScript en una página estática (`docs/simulador/index.html`). Usa los datos de 2025 de este repositorio; el detalle con las 24 jurisdicciones está en el notebook.

### Núcleo 4 — Peso de la coparticipación en las cuentas de Córdoba

![Coparticipación como % de los ingresos corrientes de Córdoba, 2015-2025](output/figures/dependencia_fiscal_cordoba.png)

El ratio da igual en pesos nominales o reales; para ver por qué se movió hay que mirar los niveles en pesos constantes. La recaudación propia se estancó justo cuando la coparticipación crecía:

![Recaudación propia y coparticipación de Córdoba, en pesos constantes base 2016](output/figures/dependencia_fiscal_cordoba_real.png)

### Núcleo 5 — Las 24 jurisdicciones comparadas

Cuántas veces se multiplicó la coparticipación real de cada jurisdicción entre 2003 y 2025. Veintidós quedan entre x3,10 y x3,20: dentro del régimen, ninguna creció mucho más rápido que otra.

![Cuántas veces se multiplicó la coparticipación real de cada jurisdicción, 2003-2025](output/figures/provincias_multiplicador_real_2003_2025.png)

Los cambios en la porción de cada una vienen de cambios de reglas puntuales: el Fondo del Conurbano congelado (Buenos Aires), el Decreto 194/2016 y la Ley 27.606 (CABA), y el Consenso Fiscal de 2018:

![Cambio en la participación de cada jurisdicción en el reparto, contra 2003](output/figures/provincias_participacion_2003_2025.png)

## Simulador interactivo

El Núcleo 3 tiene un simulador interactivo (slider de `ipywidgets`) dentro de `notebooks/03_simulador_sensibilidad.ipynb`, más la versión web linkeada arriba. Elegí `ipywidgets` en vez de una app Streamlit para que todo el proyecto se pudiera reproducir desde los notebooks sin depender de un servidor; la lógica (`scripts/simulator.py`) está separada y sin dependencias de notebook, así que la versión web es solo esa misma fórmula en JavaScript.

## Estructura del repositorio

```
data/raw/          # Datos crudos, tal como se obtuvieron. Nunca se editan a mano.
data/processed/    # Datos limpios, generados por los scripts de scripts/.
scripts/           # Procesamiento de cada núcleo, simulador y tests (simulador + consistencia de datos).
notebooks/         # Un notebook por núcleo temático, con los gráficos e interpretación.
docs/              # Metodología, y el simulador web (docs/simulador/, publicado con GitHub Pages).
output/figures/    # Gráficos exportados (PNG), embebidos en este README y en los notebooks.
run_all.py         # Corre todo el pipeline de procesamiento + notebooks con un solo comando.
```

## Fuentes de datos

| Fuente | Organismo | Núcleo(s) |
|---|---|---|
| [Coparticipación / Recursos de Origen Nacional (RON)](https://www.argentina.gob.ar/economia/sechacienda/asuntosprovinciales/ron) | Secretaría de Hacienda, Ministerio de Economía de la Nación | 1, 3, 4, 5 |
| [Índice de Precios al Consumidor, 2016-2025](https://www.indec.gob.ar/ftp/cuadros/economia/serie_ipc_divisiones.csv) | INDEC | 1 |
| Índice de Precios al Consumidor, 2003-2015 (archivo propio, sin URL pública verificada) | Fundación Norte y Sur / Orlando J. Ferreres | 1 |
| Producto Bruto Geográfico por provincia (`Jurisdiccion_52sectores.xlsx`, archivo propio) | CEPAL, sobre metodología base de INDEC | 2 |
| Índices de distribución de la coparticipación federal (`indices_copa_2018.pdf`, archivo propio) | Documento tipo Secretaría de Hacienda / BNA | 2, 3, 4, 5 |
| Recaudación provincial (`serie_recaudacion_provincial.xlsx`, archivo propio) | Dirección General de Rentas de Córdoba | 4 |

Ninguna de estas fuentes tiene una licencia restrictiva conocida para este tipo de análisis (son estadísticas públicas o compilaciones a las que ya tenía acceso), pero no todas tienen una URL pública verificada de origen. El detalle de cómo conseguí cada archivo, con qué alcance temporal y qué limitaciones tiene, está en [`data/raw/README.md`](data/raw/README.md) y en [`docs/methodology.md`](docs/methodology.md).

**Atribución**: la serie de precios 2003-2015 usada en el Núcleo 1 se basa en la compilación histórica de series económicas de Argentina realizada por **Orlando J. Ferreres** para la **Fundación Norte y Sur**, conocido por su obra de referencia *"Dos siglos de Economía Argentina"*. La uso acá solo como insumo — un índice de precios empalmado con fuentes oficiales, con el detalle en la metodología — y no reclamo ninguna autoría sobre la compilación original.

## Cómo correr el proyecto de punta a punta

```bash
# Clonar el repositorio
git clone https://github.com/llorenzomagnano-sys/analisis-de-la-coparticipacion-federal-con-foco-en-cordoba.git
cd analisis-de-la-coparticipacion-federal-con-foco-en-cordoba

# Crear y activar un entorno virtual
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Correr todo el pipeline: procesamiento de los 5 núcleos + tests + regeneración
# de los 5 notebooks (con sus gráficos). data/raw/ ya viene poblada en el repo.
python run_all.py
```

Para explorar de forma interactiva en vez de solo regenerar: `jupyter notebook` y abrir cualquiera de los notebooks de `notebooks/`. Para correr solo los tests (simulador y chequeos de consistencia de los datos procesados): `pytest scripts/`.

## Limitaciones metodológicas (resumen)

Cada una de estas se documenta en detalle, con la decisión tomada y su razón, en [`docs/methodology.md`](docs/methodology.md):

- **Núcleo 1** no llega a 1990 (la idea original) porque no existe una fuente de montos nominales de coparticipación por provincia para 1990-2002; el rango quedó en 2003-2025. El tramo 2003-2016 depende de un IPC empalmado con una fuente privada (Ferreres/Norte y Sur), porque el IPC oficial de 2007-2015 quedó desacreditado por la intervención del INDEC y el actual recién arranca en diciembre de 2016. Hacienda cambió varias veces la forma de informar la coparticipación (bruta o neta del Financiamiento Educativo, Ganancias aparte hasta 2017); la serie las unifica en una sola definición, que para Córdoba coincide con la de la propia provincia en todos los años 2015-2025.
- **Núcleo 2** usa el PBG como proxy del aporte tributario real, que tiene un problema de atribución geográfica conocido: las empresas suelen tributar donde tienen sede fiscal, no donde generan la actividad económica. Eso probablemente infla el aporte de CABA y subestima el de provincias productivas como Córdoba.
- **Núcleo 3** es un modelo lineal y proporcional, calibrado con una sola cifra pública (un cuatrimestre de recaudación). Es una calculadora de escenarios, no un modelo validado contra una serie independiente.
- **Núcleo 4** usa como proxy de "ingresos corrientes totales" de Córdoba la recaudación administrada por la Dirección General de Rentas, que excluye lo recaudado por otros organismos provinciales como EPEC. El indicador de sensibilidad es una simplificación de primera ronda: no modela ninguna respuesta de política provincial ante una caída de ingresos.
- **Núcleo 5** compara montos totales, no por habitante, porque el repositorio no tiene datos de población por provincia. El 1,55% adicional que Nación transfiere a CABA por la cautelar de 2022 no aparece en la serie de Hacienda que uso.

## Licencia

Este proyecto está bajo licencia MIT. Ver [LICENSE](LICENSE) para más detalles. Los datos de `data/raw/` conservan la licencia/términos de sus fuentes originales (estadísticas públicas u organismos oficiales); no se redistribuyen bajo la licencia MIT del código.

## Autor

**Lorenzo Magnano**

El código lo escribí con asistencia de herramientas de IA. Las preguntas, la elección y el control de las fuentes y los criterios metodológicos son míos.
