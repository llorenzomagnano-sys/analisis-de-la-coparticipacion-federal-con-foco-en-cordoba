"""
Núcleo 2 — Compara, para cada provincia, cuánto "aporta" (proxy: % de su PBG sobre el
PBG de las 24 jurisdicciones) contra cuánto "recibe" (% de lo que se reparte entre las 24
jurisdicciones según los coeficientes de la Ley 23.548).

Notas (detalle completo en docs/methodology.md):
- Coeficientes de la Ley 23.548 tal como figuran en
  data/raw/coeficientes/indices_copa_2018.pdf, con un solo ajuste: CABA en 1,4% (régimen
  automático vigente desde 2020) en vez del 3,75% de ese documento de 2018. Por una
  cautelar de la Corte Suprema (dic-2022), Nación le transfiere aparte otro 1,55%; eso
  queda fuera del coeficiente y se discute en el notebook.
- Los 24 coeficientes suman ~0,59 de la masa coparticipable total (el resto es Nación y
  el Fondo ATN). Para comparar contra el PBG, que suma 100% entre provincias, se
  renormalizan: `pct_coparticipacion_entre_provincias = coef / suma(coefs)`. Sin ese
  paso, toda provincia queda con brecha negativa en proporción a su tamaño y el ranking
  mide escala, no reparto.
- PBG 2024 (el año más reciente de la fuente, preliminar), como % de la suma de las 24
  jurisdicciones (sin la fila "No distribuido" de la fuente).
- El PBG es un PROXY del aporte tributario: las grandes empresas tributan donde tienen
  sede fiscal (muchas veces CABA), no necesariamente donde generan la actividad.
"""
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
from coeficientes_ley23548 import COEFICIENTES_COPARTICIPACION  # noqa: E402

PBG_PATH = BASE_DIR / "data" / "raw" / "pbg" / "Jurisdiccion_52sectores.xlsx"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "aporte_vs_recibo.csv"

PBG_YEAR = 2024

# Nombres tal como aparecen en la hoja VABpb -> nombre canónico usado en el proyecto.
PROVINCIA_CANONICA = {
    "Ciudad de Buenos Aires": "CABA",
    "Buenos Aires": "Buenos Aires",
    "Catamarca": "Catamarca",
    "Córdoba": "Córdoba",
    "Corrientes": "Corrientes",
    "Chaco": "Chaco",
    "Chubut": "Chubut",
    "Entre Ríos": "Entre Ríos",
    "Formosa": "Formosa",
    "Jujuy": "Jujuy",
    "La Pampa": "La Pampa",
    "La Rioja": "La Rioja",
    "Mendoza": "Mendoza",
    "Misiones": "Misiones",
    "Neuquén": "Neuquén",
    "Río Negro": "Río Negro",
    "Salta": "Salta",
    "San Juan": "San Juan",
    "San Luis": "San Luis",
    "Santa Cruz": "Santa Cruz",
    "Santa Fe": "Santa Fe",
    "Santiago del Estero": "Santiago del Estero",
    "Tucumán": "Tucumán",
    "Tierra del Fuego": "Tierra del Fuego",
}


def load_pbg_pct(year: int) -> pd.DataFrame:
    raw = pd.read_excel(PBG_PATH, sheet_name="VABpb", header=None)

    header_row = raw[raw[1] == "JURISDICCIÓN"].index[0]
    years_row = raw.iloc[header_row]
    year_columns = {}
    for col in raw.columns[2:]:
        value = years_row[col]
        if pd.isna(value):
            continue
        year_int = int(str(value).split()[0].split(".")[0])
        year_columns[year_int] = col

    if year not in year_columns:
        raise SystemExit(f"No se encontró la columna del año {year} en {PBG_PATH}.")
    col = year_columns[year]

    data = raw.iloc[header_row + 1 :, [1, col]].copy()
    data.columns = ["jurisdiccion", "pbg"]
    data = data.dropna(subset=["jurisdiccion"])
    data["jurisdiccion"] = data["jurisdiccion"].astype(str).str.strip()

    data = data[data["jurisdiccion"].isin(PROVINCIA_CANONICA)]
    if len(data) != len(PROVINCIA_CANONICA):
        faltantes = set(PROVINCIA_CANONICA) - set(data["jurisdiccion"])
        raise SystemExit(f"Jurisdicciones que no aparecen en {PBG_PATH}: {sorted(faltantes)}")

    # Participación sobre la suma de las 24, no sobre la fila "Total" de la fuente, que
    # incluye además lo "No distribuido" entre jurisdicciones (~0,06%): así suma 100%, igual
    # que la porción del reparto contra la que se compara.
    data["provincia"] = data["jurisdiccion"].map(PROVINCIA_CANONICA)
    data["pct_pbg_aporte"] = data["pbg"].astype(float) / data["pbg"].astype(float).sum()

    return data[["provincia", "pct_pbg_aporte"]]


def main() -> None:
    pbg = load_pbg_pct(PBG_YEAR)

    coef = pd.DataFrame(
        {
            "provincia": list(COEFICIENTES_COPARTICIPACION.keys()),
            "pct_coparticipacion_recibe": list(COEFICIENTES_COPARTICIPACION.values()),
        }
    )

    combinado = pbg.merge(coef, on="provincia", how="outer", indicator=True)
    solo_un_lado = combinado[combinado["_merge"] != "both"]
    if not solo_un_lado.empty:
        raise SystemExit(
            "Hay provincias que aparecen en una fuente pero no en la otra -- revisar "
            f"mapeo de nombres antes de continuar:\n{solo_un_lado}"
        )
    combinado = combinado.drop(columns="_merge")

    combinado["pct_coparticipacion_entre_provincias"] = (
        combinado["pct_coparticipacion_recibe"] / combinado["pct_coparticipacion_recibe"].sum()
    )
    combinado["diferencia_pp"] = (
        combinado["pct_coparticipacion_entre_provincias"] - combinado["pct_pbg_aporte"]
    ) * 100

    combinado = combinado.sort_values("diferencia_pp", ascending=False).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    combinado.to_csv(OUTPUT_PATH, index=False)
    print(f"Guardado: {OUTPUT_PATH} ({len(combinado)} filas)")
    print(f"PBG usado: año {PBG_YEAR}")
    print("\nCórdoba:")
    print(combinado[combinado["provincia"] == "Córdoba"].to_string(index=False))


if __name__ == "__main__":
    main()
