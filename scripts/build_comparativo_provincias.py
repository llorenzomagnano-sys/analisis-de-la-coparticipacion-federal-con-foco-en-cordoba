"""
Núcleo 5 — Las 24 jurisdicciones comparadas.

Parte de la misma serie del Núcleo 1 (`data/processed/coparticipacion_real.csv`) y arma,
para cada provincia y CABA:

  - `multiplicador_real_2003_2025`: coparticipación real 2025 / real 2003.
  - `participacion_2003`, `participacion_2025`: % de lo que se repartió entre las 24
    jurisdicciones ese año (sobre montos nominales; el deflactor es común y se cancela).
  - `coeficiente_legal_renormalizado`: coeficiente de la Ley 23.548 / suma de los 24
    (misma base que el Núcleo 2), para comparar contra lo efectivamente recibido.
  - `brecha_vs_coeficiente_pp`: participación 2025 menos coeficiente renormalizado, en
    puntos porcentuales.
  - `participacion_2025_sin_compensacion`: la misma participación sin la compensación
    del Consenso Fiscal (Ley 27.429), que es un monto fijado por provincia y no sigue
    los coeficientes. Sin ella, cada jurisdicción recibe prácticamente su coeficiente
    legal, así que la brecha sale casi entera de esa compensación.
  - `peso_compensacion_2025`: qué parte de lo que recibió cada jurisdicción en 2025 fue
    esa compensación.
  - `caida_real_desde_maximo`: coparticipación real 2025 contra el máximo de la serie.
  - `poblacion_2022`: población del Censo 2022 (INDEC, resultados definitivos).
  - `per_capita_2022_pesos_2025`: coparticipación 2022 por habitante, llevada a pesos de
    2025 con el IPC. Se mide en 2022 porque es el año del censo: dividir montos de 2025
    por población de 2022 mezclaría años, y no hay proyecciones oficiales por provincia
    basadas en el Censo 2022 en el repositorio.
  - `indice_per_capita_2022`: lo mismo relativo al promedio de las 24 jurisdicciones
    (promedio = 1). Es igual a participación 2022 / participación en la población.

Salida: data/processed/comparativo_provincias.csv
"""
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
from coeficientes_ley23548 import COEFICIENTES_COPARTICIPACION  # noqa: E402
from process_coparticipacion import load_ron_por_concepto  # noqa: E402

COPART_PATH = BASE_DIR / "data" / "processed" / "coparticipacion_real.csv"
POBLACION_PATH = BASE_DIR / "data" / "raw" / "poblacion" / "c2022_tp_est_c1.xlsx"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "comparativo_provincias.csv"

ANIO_INICIAL = 2003
ANIO_FINAL = 2025
ANIO_CENSO = 2022
CONCEPTO_COMPENSACION = "consenso fiscal ley 27429 compensacion"

# Nombres del cuadro de INDEC que no coinciden con los del resto del repositorio.
NOMBRES_INDEC = {
    "Ciudad Autónoma de Buenos Aires": "CABA",
    "Tierra del Fuego, Antártida e Islas del Atlántico Sur (1)": "Tierra del Fuego",
}


def load_poblacion_censo_2022() -> pd.Series:
    """Población 2022 por jurisdicción, del Cuadro 1 del Censo 2022 (INDEC).

    El cuadro intercala dos subtotales de Buenos Aires (24 partidos del GBA y resto) sin
    código de jurisdicción; se descartan. Se controla que las 24 sumen el total del país.
    """
    cuadro = pd.read_excel(POBLACION_PATH, sheet_name="Cuadro 1 ", header=None)
    cuadro = cuadro.iloc[:, [0, 1, 3]]
    cuadro.columns = ["codigo", "jurisdiccion", "poblacion"]
    total = cuadro.loc[cuadro["jurisdiccion"] == "Total", "poblacion"]
    con_codigo = cuadro["codigo"].astype(str).str.strip().str.fullmatch(r"\d+")
    filas = cuadro[con_codigo & cuadro["poblacion"].notna()]
    poblacion = (
        filas.assign(provincia=filas["jurisdiccion"].replace(NOMBRES_INDEC))
        .set_index("provincia")["poblacion"].astype(int)
    )
    if len(total) != 1 or len(poblacion) != 24 or poblacion.sum() != int(total.iloc[0]):
        raise SystemExit("El cuadro de población del Censo 2022 no tiene la estructura esperada.")
    return poblacion


def participaciones_anuales() -> pd.DataFrame:
    """Participación de cada jurisdicción en el total repartido entre las 24, por año
    (filas: años, columnas: jurisdicciones; cada fila suma 1)."""
    df = pd.read_csv(COPART_PATH)
    nominal = df.pivot(index="anio", columns="provincia", values="monto_nominal")
    return nominal.div(nominal.sum(axis=1), axis=0)


def compensacion_consenso_fiscal(anio: int) -> pd.DataFrame:
    """Coparticipación de `anio` por jurisdicción, separando la compensación del Consenso
    Fiscal del resto (columnas: total, compensacion, sin_compensacion; millones de $)."""
    df = load_ron_por_concepto()
    df = df[df["anio"] == anio]
    total = df.groupby("provincia")["monto"].sum()
    compensacion = (
        df[df["impuesto"] == CONCEPTO_COMPENSACION].groupby("provincia")["monto"].sum()
        .reindex(total.index, fill_value=0.0)
    )
    return pd.DataFrame(
        {"total": total, "compensacion": compensacion, "sin_compensacion": total - compensacion}
    )


def build_comparativo() -> pd.DataFrame:
    df = pd.read_csv(COPART_PATH)
    real = df.pivot(index="anio", columns="provincia", values="monto_real_base2016")
    participacion = participaciones_anuales()

    coeficientes = pd.Series(COEFICIENTES_COPARTICIPACION)
    if set(coeficientes.index) != set(real.columns):
        raise SystemExit("Las jurisdicciones de los coeficientes y de la serie no coinciden.")

    tabla = pd.DataFrame(
        {
            "real_2003_millones": real.loc[ANIO_INICIAL],
            "real_2025_millones": real.loc[ANIO_FINAL],
            "multiplicador_real_2003_2025": real.loc[ANIO_FINAL] / real.loc[ANIO_INICIAL],
            "participacion_2003": participacion.loc[ANIO_INICIAL],
            "participacion_2025": participacion.loc[ANIO_FINAL],
            "coeficiente_legal_renormalizado": coeficientes / coeficientes.sum(),
            "anio_maximo_real": real.idxmax(),
            "caida_real_desde_maximo": real.loc[ANIO_FINAL] / real.max() - 1,
        }
    )
    tabla["cambio_participacion_pp"] = (tabla["participacion_2025"] - tabla["participacion_2003"]) * 100
    tabla["brecha_vs_coeficiente_pp"] = (
        tabla["participacion_2025"] - tabla["coeficiente_legal_renormalizado"]
    ) * 100
    montos_final = compensacion_consenso_fiscal(ANIO_FINAL)
    tabla["participacion_2025_sin_compensacion"] = (
        montos_final["sin_compensacion"] / montos_final["sin_compensacion"].sum()
    )
    tabla["peso_compensacion_2025"] = montos_final["compensacion"] / montos_final["total"]

    poblacion = load_poblacion_censo_2022()
    if set(poblacion.index) != set(real.columns):
        raise SystemExit("Las jurisdicciones del Censo 2022 y de la serie no coinciden.")
    nominal = df.pivot(index="anio", columns="provincia", values="monto_nominal")
    ipc = df.groupby("anio")["ipc_promedio_anual"].first()
    censo_pesos_final = nominal.loc[ANIO_CENSO] * 1e6 * ipc.loc[ANIO_FINAL] / ipc.loc[ANIO_CENSO]
    tabla["poblacion_2022"] = poblacion
    tabla["per_capita_2022_pesos_2025"] = censo_pesos_final / poblacion
    tabla["indice_per_capita_2022"] = tabla["per_capita_2022_pesos_2025"] / (
        censo_pesos_final.sum() / poblacion.sum()
    )
    tabla.index.name = "provincia"
    return tabla.sort_values("multiplicador_real_2003_2025").reset_index()


def main() -> None:
    tabla = build_comparativo()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(OUTPUT_PATH, index=False)
    print(f"Guardado: {OUTPUT_PATH} ({len(tabla)} filas)")
    print(tabla.to_string(index=False))


if __name__ == "__main__":
    main()
