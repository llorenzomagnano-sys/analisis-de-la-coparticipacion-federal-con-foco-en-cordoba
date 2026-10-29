"""
Población por jurisdicción, para medir la coparticipación por habitante (Núcleos 1 y 5).

Fuentes (INDEC, versionadas en data/raw/poblacion/):
  - Censos 2001 y 2010: Cuadro 8 del Tomo 1 de resultados definitivos del Censo 2010,
    transcripto en `censos_2001_2010_cuadro8.csv`.
  - Censo 2022: Cuadro 1 de resultados definitivos (`c2022_tp_est_c1.xlsx`), que trae
    también la columna 2010 y sirve para controlar la transcripción.

Población de cada año (`poblacion_anual`): crecimiento a tasa constante (geométrica)
entre las fechas de los censos, evaluado a mitad de año. Los censos fueron el 17 de
noviembre de 2001, el 27 de octubre de 2010 y el 18 de mayo de 2022. Después del último
censo se extiende la tasa 2010-2022 de cada jurisdicción. Es un supuesto declarado: la
natalidad cayó mucho en esos años, así que la población 2023-2025 probablemente quede
algo sobreestimada y la coparticipación por habitante de esos años, algo subestimada.
No hay en el repositorio proyecciones oficiales basadas en el Censo 2022.
"""
from datetime import date
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
CENSO_2022_PATH = BASE_DIR / "data" / "raw" / "poblacion" / "c2022_tp_est_c1.xlsx"
CENSOS_2001_2010_PATH = BASE_DIR / "data" / "raw" / "poblacion" / "censos_2001_2010_cuadro8.csv"

TOTAL_PAIS = {2001: 36_260_130, 2010: 40_117_096, 2022: 45_892_285}
FECHAS_CENSO = {2001: date(2001, 11, 17), 2010: date(2010, 10, 27), 2022: date(2022, 5, 18)}

# Nombres de INDEC que no coinciden con los del resto del repositorio.
NOMBRES_INDEC = {
    "Ciudad Autónoma de Buenos Aires": "CABA",
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur (1)": "Tierra del Fuego",
}


def _anio_decimal(fecha: date) -> float:
    return fecha.year + (fecha.timetuple().tm_yday - 1) / 365


def load_cuadro_censo_2022() -> pd.DataFrame:
    """Columnas 2010 y 2022 del Cuadro 1 del Censo 2022, por jurisdicción.

    El cuadro intercala dos subtotales de Buenos Aires (24 partidos del GBA y resto) sin
    código de jurisdicción; se descartan. Se controla que las 24 sumen el total del país.
    """
    cuadro = pd.read_excel(CENSO_2022_PATH, sheet_name="Cuadro 1 ", header=None)
    cuadro = cuadro.iloc[:, [0, 1, 2, 3]]
    cuadro.columns = ["codigo", "jurisdiccion", 2010, 2022]
    con_codigo = cuadro["codigo"].astype(str).str.strip().str.fullmatch(r"\d+")
    filas = cuadro[con_codigo & cuadro[2022].notna()]
    tabla = (
        filas.assign(provincia=filas["jurisdiccion"].replace(NOMBRES_INDEC))
        .set_index("provincia")[[2010, 2022]].astype(int)
    )
    total = cuadro.loc[cuadro["jurisdiccion"] == "Total", [2010, 2022]]
    if len(total) != 1 or len(tabla) != 24 or (tabla.sum() != total.iloc[0].astype(int)).any():
        raise SystemExit("El cuadro de población del Censo 2022 no tiene la estructura esperada.")
    return tabla


def load_poblacion_censo_2022() -> pd.Series:
    """Población 2022 por jurisdicción (Censo 2022)."""
    return load_cuadro_censo_2022()[2022]


def load_censos() -> pd.DataFrame:
    """Población de los censos 2001, 2010 y 2022 por jurisdicción (columnas: años)."""
    transcripcion = pd.read_csv(CENSOS_2001_2010_PATH).set_index("jurisdiccion")
    transcripcion = transcripcion.rename(index={"Ciudad Autónoma de Buenos Aires": "CABA"})
    total = transcripcion.loc["Total del país"]
    provincias = transcripcion.drop("Total del país")
    provincias.columns = [2001, 2010]

    cuadro_2022 = load_cuadro_censo_2022()
    censos = provincias.join(cuadro_2022[[2022]], how="outer")
    if censos.isna().any().any() or len(censos) != 24:
        raise SystemExit("Las jurisdicciones de los censos 2001-2010 y 2022 no coinciden.")
    totales_transcriptos = {2001: total["poblacion_2001"], 2010: total["poblacion_2010"]}
    if any(totales_transcriptos[a] != TOTAL_PAIS[a] for a in totales_transcriptos) or (
        censos.sum() != pd.Series(TOTAL_PAIS)
    ).any():
        raise SystemExit("Las jurisdicciones no suman el total del país en algún censo.")
    if (censos[2010] != cuadro_2022[2010].reindex(censos.index)).any():
        raise SystemExit("La población 2010 transcripta no coincide con la del Cuadro 1 del Censo 2022.")
    return censos.astype(int).rename_axis("provincia")


def poblacion_anual(anios) -> pd.DataFrame:
    """Población estimada a mitad de cada año (filas: años, columnas: jurisdicciones)."""
    censos = load_censos()
    t = {anio: _anio_decimal(fecha) for anio, fecha in FECHAS_CENSO.items()}
    filas = {}
    for anio in anios:
        momento = anio + 0.5
        # Tramo intercensal que contiene al año; antes de 2001 o después de 2022 se usa el
        # tramo más cercano (extrapolación con su tasa).
        inicio, fin = (2001, 2010) if momento < t[2010] else (2010, 2022)
        tasa = (censos[fin] / censos[inicio]) ** (1 / (t[fin] - t[inicio]))
        filas[anio] = censos[inicio] * tasa ** (momento - t[inicio])
    return pd.DataFrame(filas).T.rename_axis("anio")
