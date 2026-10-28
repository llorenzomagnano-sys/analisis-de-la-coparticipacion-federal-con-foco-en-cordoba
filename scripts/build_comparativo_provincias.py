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

La comparación es en montos totales, no per cápita: el repositorio no tiene datos de
población por provincia (ver docs/methodology.md).

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
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "comparativo_provincias.csv"

ANIO_INICIAL = 2003
ANIO_FINAL = 2025
CONCEPTO_COMPENSACION = "consenso fiscal ley 27429 compensacion"


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
