"""
Núcleo 4 (complemento) — La dependencia de Córdoba contra la de las demás provincias.

El ratio principal del Núcleo 4 sale del archivo de Rentas de Córdoba, que no existe con
el mismo formato para las otras provincias. Para comparar uso la ejecución presupuestaria
de la Administración Pública No Financiera de cada jurisdicción (esquema
ahorro-inversión-financiamiento, base caja) que publica la Dirección Nacional de
Coordinación Fiscal con las Provincias: 2005-2025, en millones de pesos corrientes, con
el mismo formato para las 24.

Indicadores, para cada jurisdicción y año:

  - `origen_nacional_sobre_ingresos_corrientes`: recursos tributarios de origen nacional
    (coparticipación y los demás regímenes automáticos) sobre ingresos corrientes. Es lo
    más parecido al ratio del Núcleo 4, pero contra el presupuesto entero en vez de
    contra la recaudación que administra Rentas.
  - `transferencias_nacionales_sobre_ingresos` (indicador principal): recursos de origen
    nacional más transferencias corrientes y de capital recibidas, sobre ingresos totales
    sin las contribuciones a la seguridad social. Las contribuciones se sacan del
    denominador porque solo las registran las provincias que conservan su caja de
    jubilaciones (Córdoba entre ellas): con ellas adentro, esas provincias parecerían
    menos dependientes solo por tener caja propia.
  - `tributarios_propios_sobre_ingresos`: recursos tributarios de origen provincial sobre
    el mismo denominador (autonomía tributaria).

Las transferencias recibidas vienen casi todas de Nación, pero el esquema no las abre
por origen. Un año sin datos en la fuente (ingresos en cero: La Pampa en 2025) queda
afuera, sin completar.

Salida: data/processed/dependencia_provincias.csv (una fila por jurisdicción y año).
"""
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
AIF_PATH = (
    BASE_DIR / "data" / "raw" / "ejecucion_presupuestaria_provincial" / "serie_aif-apnf-2025.xlsx"
)
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "dependencia_provincias.csv"

# Nombre de la hoja -> nombre canónico del repositorio.
HOJAS = {
    "Ciudad": "CABA", "Buenos Aires": "Buenos Aires", "Catamarca": "Catamarca", "Córdoba": "Córdoba",
    "Corrientes": "Corrientes", "Chaco": "Chaco", "Chubut": "Chubut", "Entre Ríos": "Entre Ríos",
    "Formosa": "Formosa", "Jujuy": "Jujuy", "La Pampa": "La Pampa", "La Rioja": "La Rioja",
    "Mendoza": "Mendoza", "Misiones": "Misiones", "Neuquén": "Neuquén", "Río Negro": "Río Negro",
    "Salta": "Salta", "San Juan": "San Juan", "San Luis": "San Luis", "Santa Cruz": "Santa Cruz",
    "Santa Fe": "Santa Fe", "Santiago del  Estero": "Santiago del Estero", "Tucumán": "Tucumán",
    "Tierra del Fuego": "Tierra del Fuego",
}

# Filas del esquema, identificadas por su texto (y por orden de aparición cuando el texto
# se repite: "Transferencias Corrientes" y "Transferencias de Capital" aparecen primero
# entre los ingresos y después entre los gastos).
FILAS = {
    "ingresos_corrientes": ("I. INGRESOS CORRIENTES", 0),
    "tributarios_origen_provincial": ("- De Orígen Provincial", 0),
    "tributarios_origen_nacional": ("- De Orígen Nacional", 0),
    "ley23548_y_financiamiento_educativo": ("- Sub - Total", 0),
    "contribuciones_seguridad_social": (". Contribuciones a la Seguridad Social", 0),
    "transferencias_corrientes_recibidas": (". Transferencias Corrientes", 0),
    "transferencias_capital_recibidas": (". Transferencias de Capital", 0),
    "ingresos_totales": ("VI. INGRESOS TOTALES (I+IV)", 0),
}


def load_hoja(hoja: str) -> pd.DataFrame:
    """Las filas de FILAS de una hoja, por año (millones de pesos corrientes)."""
    cuadro = pd.read_excel(AIF_PATH, sheet_name=hoja, header=None, engine="calamine")
    etiquetas = cuadro[0].astype(str).str.strip()
    encabezado = etiquetas.index[etiquetas == "CONCEPTO"]
    if len(encabezado) != 1:
        raise SystemExit(f"La hoja {hoja!r} no tiene la estructura esperada.")
    anios = cuadro.iloc[encabezado[0], 1:].dropna().astype(int)

    datos = {}
    for columna, (texto, orden) in FILAS.items():
        filas = etiquetas.index[etiquetas == texto]
        if len(filas) <= orden:
            raise SystemExit(f"No se encontró la fila {texto!r} en la hoja {hoja!r}.")
        datos[columna] = cuadro.loc[filas[orden], anios.index].astype(float).to_numpy()
    return pd.DataFrame(datos, index=pd.Index(anios.to_numpy(), name="anio"))


def build_dependencia() -> pd.DataFrame:
    tablas = []
    for hoja, provincia in HOJAS.items():
        tabla = load_hoja(hoja)
        sin_datos = tabla.index[tabla["ingresos_corrientes"] <= 0]
        for anio in sin_datos:
            print(f"AVISO: {provincia} no tiene datos en {anio}; queda afuera de ese año.")
        tablas.append(tabla.drop(sin_datos).assign(provincia=provincia).reset_index())
    df = pd.concat(tablas, ignore_index=True)

    base = df["ingresos_totales"] - df["contribuciones_seguridad_social"]
    transferencias = (
        df["tributarios_origen_nacional"] + df["transferencias_corrientes_recibidas"]
        + df["transferencias_capital_recibidas"]
    )
    df["origen_nacional_sobre_ingresos_corrientes"] = (
        df["tributarios_origen_nacional"] / df["ingresos_corrientes"]
    )
    df["transferencias_nacionales_sobre_ingresos"] = transferencias / base
    df["tributarios_propios_sobre_ingresos"] = df["tributarios_origen_provincial"] / base
    columnas = ["provincia", "anio"] + list(FILAS) + [
        "origen_nacional_sobre_ingresos_corrientes", "transferencias_nacionales_sobre_ingresos",
        "tributarios_propios_sobre_ingresos",
    ]
    return df[columnas].sort_values(["provincia", "anio"]).reset_index(drop=True)


def agregado_por_anio(df: pd.DataFrame) -> pd.DataFrame:
    """Los mismos indicadores para el conjunto de jurisdicciones con datos cada año
    (cocientes de sumas, o sea, ponderados por tamaño)."""
    sumas = df.groupby("anio")[list(FILAS)].sum()
    base = sumas["ingresos_totales"] - sumas["contribuciones_seguridad_social"]
    return pd.DataFrame({
        "jurisdicciones": df.groupby("anio")["provincia"].count(),
        "origen_nacional_sobre_ingresos_corrientes": (
            sumas["tributarios_origen_nacional"] / sumas["ingresos_corrientes"]
        ),
        "transferencias_nacionales_sobre_ingresos": (
            sumas["tributarios_origen_nacional"] + sumas["transferencias_corrientes_recibidas"]
            + sumas["transferencias_capital_recibidas"]
        ) / base,
        "tributarios_propios_sobre_ingresos": sumas["tributarios_origen_provincial"] / base,
    })


def main() -> None:
    df = build_dependencia()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Guardado: {OUTPUT_PATH} ({len(df)} filas)")
    ultimo = df[df["anio"] == df["anio"].max()].set_index("provincia")
    print(ultimo[["transferencias_nacionales_sobre_ingresos", "origen_nacional_sobre_ingresos_corrientes"]]
          .sort_values("transferencias_nacionales_sobre_ingresos").round(3).to_string())


if __name__ == "__main__":
    main()
