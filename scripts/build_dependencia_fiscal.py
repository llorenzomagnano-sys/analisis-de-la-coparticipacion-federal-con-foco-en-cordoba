"""
Núcleo 4 — Peso de la coparticipación en las cuentas de Córdoba.

Fuente única para el ratio: `data/raw/ingresos_cordoba/serie_recaudacion_provincial.xlsx`
(hoja "Serie_Mensual"), recaudación administrada por la Dirección General de Rentas de
Córdoba. Se leen tres filas por su código:

  - `1`     Total (Recursos de Origen Provincial + Recursos de Origen Nacional): la
            recaudación total de la provincia. Lo propio es lo que administra Rentas
            (tributos y algunos recursos no tributarios, como multas); excluye lo que
            recaudan otros organismos provinciales (p. ej., EPEC), según la nota al pie del
            archivo. No son los ingresos corrientes del presupuesto provincial, que suman
            además, por ejemplo, los aportes a la Caja de Jubilaciones y las transferencias
            no automáticas de Nación.
  - `1.1`   Recursos de Origen Provincial (recaudación propia).
  - `1.2.1` Coparticipación Federal de Impuestos: Ley 23.548 + compensación del
            Consenso Fiscal (Ley 27.429) + bono Consenso Fiscal.
  - `1.2.3` Fondo para Obras de Infraestructura y Programas Sociales (Ley 27.429, punto
            I.c del Consenso Fiscal). Hasta 2017 era la asignación específica de
            Ganancias; desde 2018 Nación la transfiere como coparticipación Ley 23.548 y
            la provincia la sigue registrando en esta fila aparte.
  - `1.2.5.1` Ley 26.075 - Financiamiento Educativo: la parte de la coparticipación que
            esa ley afecta a educación.

La coparticipación es 1.2.1 + 1.2.3 + 1.2.5.1, la misma definición que el Núcleo 1 (ver
process_coparticipacion.py). Usando solo 1.2.1 quedaría afuera más de una cuarta parte de
lo que Nación transfiere por la Ley 23.548, y una caída de la recaudación coparticipable
también se la llevaría.

RATIO (`ratio_coparticipacion_recaudacion`) = (1.2.1 + 1.2.3 + 1.2.5.1) / fila 1: numerador y
denominador del mismo archivo, así el numerador es efectivamente parte del denominador. Da
igual en pesos nominales o reales (el deflactor se cancela).

CONTROL CONTRA LA SERIE NACIONAL: `coparticipacion_ron_pesos` es la coparticipación de
Córdoba según la serie RON de Hacienda (Núcleo 1) y `diferencia_ron_vs_provincia` su
diferencia relativa contra el archivo provincial. Las dos fuentes son independientes y
coinciden todos los años 2015-2025 (diferencia menor a 2%).

COLUMNAS REALES (`*_real_pesos_2025`): pesos constantes del promedio de 2025, la misma
unidad que usan los gráficos del Núcleo 1, con el mismo IPC empalmado
(`load_ipc_empalmado`): `real = nominal × (ipc_2025 / ipc_año)`.

UNIDADES: el archivo rotula sus valores como "millones de pesos corrientes", pero están
en PESOS corrientes (la fila de coparticipación coincide en pesos con la serie RON en
2015-2017; ver docs/methodology.md).

ALCANCE: 2015-2025. El archivo arranca en enero de 2015; 2026 queda afuera por ser un
año incompleto.

Salida: data/processed/dependencia_fiscal_cordoba.csv
"""
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from coeficientes_ley23548 import COEFICIENTES_COPARTICIPACION  # noqa: E402
from simulator import simular_shock  # noqa: E402
from process_coparticipacion import load_ipc_empalmado  # noqa: E402

COPART_PATH = BASE_DIR / "data" / "processed" / "coparticipacion_real.csv"
INGRESOS_PATH = BASE_DIR / "data" / "raw" / "ingresos_cordoba" / "serie_recaudacion_provincial.xlsx"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "dependencia_fiscal_cordoba.csv"

SCOPE_START_YEAR = 2015
SCOPE_END_YEAR = 2025

MESES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}


def _parse_fecha_columna(valor):
    """Convierte el encabezado de una columna de Serie_Mensual a (año, mes).

    La mayoría de las columnas traen un datetime real, pero al menos una
    (diciembre de 2023) viene como texto ("dic-23") -- se tolera ese formato
    en vez de asumir que todas las columnas son consistentes.
    """
    if hasattr(valor, "year"):
        return valor.year, valor.month
    texto = str(valor).strip().lower()
    mes_str, anio_str = texto.split("-")
    return 2000 + int(anio_str), MESES[mes_str]


# Cada columna de salida es la suma de las filas con esos códigos.
FILAS_DGR = {
    "recaudacion_total_pesos": ["1"],
    "recursos_propios_pesos": ["1.1"],
    "coparticipacion_pesos": ["1.2.1", "1.2.3", "1.2.5.1"],
    # Compensación y bono del Consenso Fiscal (incluidos en 1.2.1): montos fijos que no
    # siguen los coeficientes, así que el simulador no los mueve con la recaudación.
    "compensacion_consenso_fiscal_pesos": ["1.2.1.2", "1.2.1.3"],
}


def load_series_dgr_mensuales() -> pd.DataFrame:
    """Filas de FILAS_DGR de Serie_Mensual, mes a mes (índice: período AAAAMM)."""
    raw = pd.read_excel(INGRESOS_PATH, sheet_name="Serie_Mensual", header=None)
    codigos = raw[0].astype(str).str.strip()

    fila_fechas = 2  # fila 3 de la hoja
    columnas_datos = [c for c in raw.columns if c >= 2]

    series = {}
    for columna_salida, codigos_fila in FILAS_DGR.items():
        montos = {}
        for codigo in codigos_fila:
            filas = codigos[codigos == codigo].index
            if len(filas) != 1:
                raise SystemExit(
                    f"Se esperaba una única fila con código {codigo} en Serie_Mensual, se "
                    f"encontraron {len(filas)}. Revisar manualmente el archivo."
                )
            fila = int(filas[0])

            for c in columnas_datos:
                fecha_cruda = raw.iat[fila_fechas, c]
                if pd.isna(fecha_cruda):
                    continue
                anio, mes = _parse_fecha_columna(fecha_cruda)
                monto = raw.iat[fila, c]
                if pd.isna(monto):
                    raise SystemExit(
                        f"Falta el dato de la fila {codigo} para {mes:02d}/{anio} en Serie_Mensual; "
                        "no se completa con supuestos. Revisar el archivo."
                    )
                periodo = anio * 100 + mes
                montos[periodo] = montos.get(periodo, 0.0) + float(monto)
        series[columna_salida] = montos

    df = pd.DataFrame(series).sort_index()
    df.index.name = "periodo"
    return df


def load_series_dgr_anuales() -> pd.DataFrame:
    """Suma por año calendario completo las filas de FILAS_DGR de Serie_Mensual."""
    mensual = load_series_dgr_mensuales()
    anio = mensual.index // 100
    meses_por_anio = pd.Series(anio).value_counts()

    anios_incompletos = sorted(meses_por_anio[meses_por_anio < 12].index)
    if anios_incompletos:
        print(
            f"AVISO: años con menos de 12 meses de datos (se descartan, no se completan "
            f"con supuestos): {anios_incompletos}"
        )

    df = mensual.groupby(anio).sum()
    df.index.name = "anio"
    df = df.reset_index()
    df = df[df["anio"].map(meses_por_anio) == 12]
    return df.sort_values("anio").reset_index(drop=True)


def build_ratio() -> pd.DataFrame:
    df = load_series_dgr_anuales()
    df = df[(df["anio"] >= SCOPE_START_YEAR) & (df["anio"] <= SCOPE_END_YEAR)].copy()

    faltantes = set(range(SCOPE_START_YEAR, SCOPE_END_YEAR + 1)) - set(df["anio"])
    if faltantes:
        print(
            f"AVISO: faltan {len(faltantes)} años en 2015-2025 (quedan ausentes en la "
            f"salida): {sorted(faltantes)}"
        )

    df["ratio_coparticipacion_recaudacion"] = df["coparticipacion_pesos"] / df["recaudacion_total_pesos"]
    df["participacion_recursos_propios"] = df["recursos_propios_pesos"] / df["recaudacion_total_pesos"]

    ipc = load_ipc_empalmado()
    ipc_2025 = float(ipc.loc[ipc["anio"] == 2025, "ipc_promedio_anual"].iloc[0])
    df = df.merge(ipc, on="anio", how="left")
    if df["ipc_promedio_anual"].isna().any():
        raise SystemExit("Falta IPC para algún año del alcance; no se deflacta con supuestos.")
    for col in ["recaudacion_total_pesos", "recursos_propios_pesos", "coparticipacion_pesos"]:
        df[col.replace("_pesos", "_real_pesos_2025")] = df[col] * ipc_2025 / df["ipc_promedio_anual"]
    df = df.drop(columns=["ipc_promedio_anual"])

    copart_ron = pd.read_csv(COPART_PATH)
    copart_ron = copart_ron[copart_ron["provincia"] == "Córdoba"][["anio", "monto_nominal"]]
    copart_ron["coparticipacion_ron_pesos"] = copart_ron["monto_nominal"] * 1e6
    df = df.merge(copart_ron.drop(columns="monto_nominal"), on="anio", how="left")
    df["diferencia_ron_vs_provincia"] = df["coparticipacion_ron_pesos"] / df["coparticipacion_pesos"] - 1

    return df.sort_values("anio").reset_index(drop=True)


def base_calibrada_cordoba(anio_referencia: int) -> tuple[float, float, float]:
    """Masa coparticipable total implícita, coparticipación y recaudación total de Córdoba.

    La masa se calibra para que el coeficiente de Córdoba aplicado sobre ella reproduzca
    exactamente la coparticipación que registra el archivo provincial en
    `anio_referencia`, sin la compensación del Consenso Fiscal (monto fijo que no sigue
    los coeficientes). Así, el impacto en pesos que devuelve `simular_shock` y el
    denominador (recaudación total) salen de la misma fuente.
    """
    ratio_df = build_ratio()
    fila = ratio_df.loc[ratio_df["anio"] == anio_referencia].iloc[0]
    coparticipacion = float(fila["coparticipacion_pesos"])
    recaudacion_total = float(fila["recaudacion_total_pesos"])
    proporcional = coparticipacion - float(fila["compensacion_consenso_fiscal_pesos"])
    recaudacion_base = proporcional / COEFICIENTES_COPARTICIPACION["Córdoba"]
    return recaudacion_base, coparticipacion, recaudacion_total


def calcular_sensibilidad(anio_referencia: int, escenarios: list[float]) -> pd.DataFrame:
    """Traduce shocks de recaudación coparticipable (Núcleo 3) en impacto % sobre el
    la recaudación total de Córdoba en `anio_referencia`."""
    recaudacion_base, _copart, recaudacion_total = base_calibrada_cordoba(anio_referencia)

    filas = []
    for variacion in escenarios:
        resultado = simular_shock(variacion, recaudacion_base, COEFICIENTES_COPARTICIPACION)
        impacto_cordoba = next(
            p["impacto_pesos"] for p in resultado["por_provincia"] if p["provincia"] == "Córdoba"
        )
        filas.append(
            {
                "variacion_pct_recaudacion": variacion,
                "impacto_copart_cordoba_pesos": impacto_cordoba,
                "impacto_pct_recaudacion_total_cordoba": impacto_cordoba / recaudacion_total,
            }
        )
    return pd.DataFrame(filas)


def main() -> None:
    ratio_df = build_ratio()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ratio_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Guardado: {OUTPUT_PATH} ({len(ratio_df)} filas)")
    print(ratio_df.to_string(index=False))

    anio_referencia = int(ratio_df["anio"].max())
    print(f"\nSensibilidad, año de referencia {anio_referencia}:")
    sensibilidad = calcular_sensibilidad(anio_referencia, [-0.05, -0.10])
    print(sensibilidad.to_string(index=False))


if __name__ == "__main__":
    main()
