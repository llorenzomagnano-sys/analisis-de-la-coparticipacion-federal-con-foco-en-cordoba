"""
Núcleo 1 (complemento) — La coparticipación en proporción a la economía y por habitante.

Un monto real que crece no dice si creció más o menos que la economía ni que la
población. Este script pone la serie del Núcleo 1 (las 24 jurisdicciones juntas y cada
una) contra el PIB y la población, y descompone su crecimiento real.

DESCOMPOSICIÓN (`descomponer`): para el total de las 24, en términos reales (deflactado
por IPC) vale la identidad

    coparticipación / IPC = PIB real × (deflactor del PIB / IPC)
                            × (masa Ley 23.548 / PIB) × (coparticipación / masa)

  - PIB real: crecimiento de la economía.
  - Deflactor del PIB / IPC: cuánto subieron los precios de lo que se produce contra los
    de lo que se consume. La recaudación sigue al PIB nominal, así que si el deflactor
    sube más que el IPC, la recaudación deflactada por IPC crece más que el PIB real.
  - Masa Ley 23.548 / PIB: todo lo que Hacienda registra como distribuido por la Ley
    23.548 (provincias, Nación, ANSES y Fondo ATN), sobre el PIB. Mide cuánto recaudan
    los impuestos coparticipables respecto del tamaño de la economía.
  - Coparticipación / masa: qué parte de esa masa llega a las 24 jurisdicciones con la
    definición del Núcleo 1. Sube cuando se devolvió el 15% que se detraía para la ANSES
    (2016-2020) y cambia con el fin de las asignaciones de Ganancias y la compensación
    del Consenso Fiscal (2018).
Dividiendo además por la población, queda la coparticipación real por habitante.

El PIB del INDEC (año base 2004) arranca en 2004, así que el % del PIB y la
descomposición cubren 2004-2025. La población sale de `poblacion.py` (interpolación
entre censos). Los montos reales están en pesos de 2025 (IPC promedio de 2025).

Salidas:
  - data/processed/coparticipacion_agregada.csv: una fila por año con el total de las 24.
  - data/processed/coparticipacion_por_habitante.csv: una fila por jurisdicción y año.
"""
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
from poblacion import poblacion_anual  # noqa: E402
from process_coparticipacion import (  # noqa: E402
    CONCEPTO_BRUTO,
    CONCEPTO_FINANCIAMIENTO_EDUCATIVO,
    RECIPIENTES_NO_PROVINCIALES,
    RON_PATH,
)

COPART_PATH = BASE_DIR / "data" / "processed" / "coparticipacion_real.csv"
PIB_PATH = BASE_DIR / "data" / "raw" / "pib_nacional" / "sh_oferta_demanda_09_26.xls"
AGREGADA_PATH = BASE_DIR / "data" / "processed" / "coparticipacion_agregada.csv"
POR_HABITANTE_PATH = BASE_DIR / "data" / "processed" / "coparticipacion_por_habitante.csv"

ANIO_PESOS = 2025
CONCEPTOS_MASA_LEY_23548 = {
    CONCEPTO_BRUTO,
    "coparticipacion federal de impuestos neta ley 26075",
    CONCEPTO_FINANCIAMIENTO_EDUCATIVO,
}


def load_pib_anual() -> pd.DataFrame:
    """PIB anual del INDEC: nominal y a precios de 2004 (millones de pesos) y deflactor
    implícito (2004 = 1). Toma la columna 'Total' de cada año de los cuadros 8 y 1."""

    def fila_pib(hoja: str) -> pd.Series:
        cuadro = pd.read_excel(PIB_PATH, sheet_name=hoja, header=None, engine="calamine")
        if str(cuadro.iloc[6, 1]).strip() != "Producto Interno Bruto":
            raise SystemExit(f"La hoja {hoja!r} del PIB no tiene la estructura esperada.")
        anios = cuadro.iloc[3].ffill()
        periodos = cuadro.iloc[4].astype(str).str.strip()
        columnas = [c for c in cuadro.columns[2:] if periodos[c] == "Total"]
        return pd.Series(
            {int(str(anios[c])[:4]): float(cuadro.iloc[6, c]) for c in columnas}
        )

    pib = pd.DataFrame({"pib_nominal_millones": fila_pib("cuadro 8"), "pib_real_millones_2004": fila_pib("cuadro 1")})
    pib["deflactor_pib_2004"] = pib["pib_nominal_millones"] / pib["pib_real_millones_2004"]
    return pib.rename_axis("anio")


def load_masa_ley_23548() -> pd.DataFrame:
    """Lo que Hacienda registra como distribuido por la Ley 23.548 (bruto, o neto más
    Financiamiento Educativo), por año: total de todos los destinatarios y la parte de
    las 24 jurisdicciones. Millones de pesos corrientes."""
    df = pd.read_csv(RON_PATH, sep=";", encoding="latin-1")
    df.columns = [c.strip().lower() for c in df.columns]
    df["monto"] = df["monto"].astype(str).str.replace(",", ".", regex=False).astype(float)
    df["provincia"] = df["provincia"].str.strip().str.lower()
    df = df[df["impuesto"].str.strip().str.lower().isin(CONCEPTOS_MASA_LEY_23548)]
    total = df.groupby("ano")["monto"].sum()
    provincias = df[~df["provincia"].isin(RECIPIENTES_NO_PROVINCIALES)].groupby("ano")["monto"].sum()
    return pd.DataFrame(
        {"masa_ley23548_millones": total, "ley23548_a_provincias_millones": provincias}
    ).rename_axis("anio")


def build_agregada() -> tuple[pd.DataFrame, pd.DataFrame]:
    copart = pd.read_csv(COPART_PATH)
    anios = sorted(copart["anio"].unique())
    ipc = copart.groupby("anio")["ipc_promedio_anual"].first()
    a_pesos_finales = ipc.loc[ANIO_PESOS] / ipc

    nominal = copart.pivot(index="anio", columns="provincia", values="monto_nominal")
    poblacion = poblacion_anual(anios)
    if set(poblacion.columns) != set(nominal.columns):
        raise SystemExit("Las jurisdicciones de la población y de la serie no coinciden.")

    por_habitante = (
        (nominal * 1e6).mul(a_pesos_finales, axis=0) / poblacion[nominal.columns]
    )
    por_habitante_largo = (
        por_habitante.stack().rename("por_habitante_pesos_2025").to_frame()
        .join(poblacion.stack().rename("poblacion_estimada"))
        .reset_index().rename(columns={"level_1": "provincia"})
        [["provincia", "anio", "poblacion_estimada", "por_habitante_pesos_2025"]]
        .sort_values(["provincia", "anio"]).reset_index(drop=True)
    )

    agregada = pd.DataFrame(
        {
            "coparticipacion_nominal_millones": nominal.sum(axis=1),
            "ipc_promedio_anual": ipc,
        }
    )
    agregada["coparticipacion_real_millones_pesos_2025"] = (
        agregada["coparticipacion_nominal_millones"] * a_pesos_finales
    )
    agregada["poblacion_estimada"] = poblacion.sum(axis=1)
    agregada["por_habitante_pesos_2025"] = (
        agregada["coparticipacion_real_millones_pesos_2025"] * 1e6 / agregada["poblacion_estimada"]
    )
    agregada = agregada.join(load_masa_ley_23548()).join(load_pib_anual())
    agregada["porcion_ley23548_a_provincias"] = (
        agregada["ley23548_a_provincias_millones"] / agregada["masa_ley23548_millones"]
    )
    agregada["coparticipacion_pct_pib"] = (
        agregada["coparticipacion_nominal_millones"] / agregada["pib_nominal_millones"] * 100
    )
    agregada["masa_ley23548_pct_pib"] = (
        agregada["masa_ley23548_millones"] / agregada["pib_nominal_millones"] * 100
    )
    return agregada.reset_index(), por_habitante_largo


def descomponer(agregada: pd.DataFrame, desde: int, hasta: int) -> pd.DataFrame:
    """Multiplicadores de cada factor de la identidad del docstring entre dos años.
    El producto de los cuatro primeros es el crecimiento real del total, y dividido por
    la población da el crecimiento real por habitante."""
    a = agregada.set_index("anio")
    if a.loc[[desde, hasta], "pib_nominal_millones"].isna().any():
        raise SystemExit(f"No hay PIB para {desde} o {hasta}; la descomposición arranca en 2004.")

    def cambio(serie: pd.Series) -> float:
        return serie.loc[hasta] / serie.loc[desde]

    factores = {
        "PIB real": cambio(a["pib_real_millones_2004"]),
        "Deflactor del PIB / IPC": cambio(a["deflactor_pib_2004"] / a["ipc_promedio_anual"]),
        "Masa Ley 23.548 / PIB": cambio(a["masa_ley23548_millones"] / a["pib_nominal_millones"]),
        "Parte de la masa que llega a las 24": cambio(
            a["coparticipacion_nominal_millones"] / a["masa_ley23548_millones"]
        ),
        "Coparticipación real (total)": cambio(a["coparticipacion_real_millones_pesos_2025"]),
        "Población": cambio(a["poblacion_estimada"]),
        "Coparticipación real por habitante": cambio(a["por_habitante_pesos_2025"]),
    }
    return pd.Series(factores, name=f"multiplicador_{desde}_{hasta}").rename_axis("factor").to_frame()


def main() -> None:
    agregada, por_habitante = build_agregada()
    AGREGADA_PATH.parent.mkdir(parents=True, exist_ok=True)
    agregada.to_csv(AGREGADA_PATH, index=False)
    por_habitante.to_csv(POR_HABITANTE_PATH, index=False)
    print(f"Guardado: {AGREGADA_PATH} ({len(agregada)} filas)")
    print(f"Guardado: {POR_HABITANTE_PATH} ({len(por_habitante)} filas)")
    print(descomponer(agregada, 2004, 2025).round(3).to_string())


if __name__ == "__main__":
    main()
