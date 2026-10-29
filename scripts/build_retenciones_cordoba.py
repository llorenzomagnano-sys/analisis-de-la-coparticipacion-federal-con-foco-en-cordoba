"""
Núcleo 2 (complemento) — Lo que la comparación con el PBG deja afuera: las retenciones.

Los derechos de exportación (retenciones) son un impuesto nacional que no se coparticipa:
van enteros al Tesoro Nacional. Para una provincia agroexportadora como Córdoba son la
parte más discutida de su relación fiscal con la Nación, y la comparación "aporte vs
recibo" del Núcleo 2 no los ve, porque solo mira el reparto de la Ley 23.548.

Este script estima qué parte de las retenciones de cada año corresponde a la producción
de Córdoba, repartiendo el total nacional según la participación de la provincia en las
exportaciones por origen provincial (INDEC):

  - Estimación principal: participación de Córdoba en las exportaciones de productos
    primarios (PP) y manufacturas de origen agropecuario (MOA). Las retenciones se
    concentran en esos rubros (el complejo sojero, los cereales, los aceites y harinas),
    y casi toda la exportación de Córdoba es de esos rubros.
  - Cota baja: participación de Córdoba en el total de las exportaciones. Le asigna a
    Córdoba parte de lo que se cobra sobre combustibles y manufacturas industriales,
    rubros con alícuotas mucho menores en los que la provincia pesa poco, así que es un
    piso razonable.

Es una estimación de orden de magnitud, no un dato: las alícuotas cambian por producto
y por año, el origen provincial de INDEC no siempre coincide con dónde se produjo el
grano, y quien soporta el impuesto (en buena medida el productor, vía un precio más
bajo) no es necesariamente quien lo paga. Detalle en docs/methodology.md.

Entradas: data/raw/fiscal_nacional/derechos_exportacion_anual.csv,
data/raw/exportaciones/exportaciones_cordoba_y_total_por_rubro.csv y la serie del
Núcleo 1 (data/processed/coparticipacion_real.csv).

Salida: data/processed/retenciones_cordoba.csv (una fila por año, 2003-2024; las
exportaciones por provincia llegan hasta 2024).
"""
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DEX_PATH = BASE_DIR / "data" / "raw" / "fiscal_nacional" / "derechos_exportacion_anual.csv"
EXPO_PATH = BASE_DIR / "data" / "raw" / "exportaciones" / "exportaciones_cordoba_y_total_por_rubro.csv"
COPART_PATH = BASE_DIR / "data" / "processed" / "coparticipacion_real.csv"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "retenciones_cordoba.csv"

ANIO_INICIAL = 2003
ANIO_PESOS = 2025

SERIES_EXPORTACIONES = {
    "350.1_TOTAL_EXPONES__39": "total_pais",
    "350.1_TOTAL_EXPO_PP__22": "pp_pais",
    "350.1_TOTAL_EXPOMOA__23": "moa_pais",
    "350.1_CORDOBA_TOOBA__21": "total_cordoba",
    "350.1_CORDOBA_PP_PP__10": "pp_cordoba",
    "350.1_CORDOBA_MOMOA__11": "moa_cordoba",
}


def _por_anio(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["anio"] = pd.to_datetime(df["indice_tiempo"]).dt.year
    return df.drop(columns="indice_tiempo").set_index("anio")


def build_retenciones() -> pd.DataFrame:
    dex = _por_anio(DEX_PATH)["142.1_DEREC_2001_A_20"].rename("retenciones_pais_millones")
    expo = _por_anio(EXPO_PATH)[list(SERIES_EXPORTACIONES)].rename(columns=SERIES_EXPORTACIONES)

    copart = pd.read_csv(COPART_PATH)
    ipc = copart.groupby("anio")["ipc_promedio_anual"].first()
    cordoba = copart[copart["provincia"] == "Córdoba"].set_index("anio")["monto_nominal"]

    anios = range(ANIO_INICIAL, int(expo.index.max()) + 1)
    faltantes = [a for a in anios if a not in dex.index or a not in cordoba.index or expo.loc[a].isna().any()]
    if faltantes:
        raise SystemExit(f"Faltan retenciones, exportaciones o coparticipación para {faltantes}.")

    tabla = pd.DataFrame(index=pd.Index(anios, name="anio"))
    tabla["retenciones_pais_millones"] = dex
    tabla["participacion_cordoba_exportaciones"] = expo["total_cordoba"] / expo["total_pais"]
    tabla["participacion_cordoba_pp_moa"] = (expo["pp_cordoba"] + expo["moa_cordoba"]) / (
        expo["pp_pais"] + expo["moa_pais"]
    )
    tabla["retenciones_cordoba_millones"] = (
        tabla["retenciones_pais_millones"] * tabla["participacion_cordoba_pp_moa"]
    )
    tabla["retenciones_cordoba_cota_baja_millones"] = (
        tabla["retenciones_pais_millones"] * tabla["participacion_cordoba_exportaciones"]
    )
    tabla["coparticipacion_cordoba_millones"] = cordoba
    tabla["retenciones_sobre_coparticipacion"] = (
        tabla["retenciones_cordoba_millones"] / tabla["coparticipacion_cordoba_millones"]
    )
    tabla["retenciones_sobre_coparticipacion_cota_baja"] = (
        tabla["retenciones_cordoba_cota_baja_millones"] / tabla["coparticipacion_cordoba_millones"]
    )
    a_pesos_finales = ipc.loc[ANIO_PESOS] / ipc.reindex(tabla.index)
    for columna in [
        "retenciones_cordoba_millones", "retenciones_cordoba_cota_baja_millones",
        "coparticipacion_cordoba_millones",
    ]:
        tabla[columna.replace("_millones", "_millones_pesos_2025")] = tabla[columna] * a_pesos_finales
    return tabla.reset_index()


def main() -> None:
    tabla = build_retenciones()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(OUTPUT_PATH, index=False)
    print(f"Guardado: {OUTPUT_PATH} ({len(tabla)} filas)")
    print(tabla[[
        "anio", "participacion_cordoba_pp_moa", "participacion_cordoba_exportaciones",
        "retenciones_sobre_coparticipacion", "retenciones_sobre_coparticipacion_cota_baja",
    ]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
