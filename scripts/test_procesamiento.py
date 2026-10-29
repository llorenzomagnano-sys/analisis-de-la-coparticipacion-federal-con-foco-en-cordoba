"""Chequeos de consistencia del procesamiento de datos (Núcleos 1, 2, 4 y 5).

Leen los datos versionados en data/raw/ y data/processed/. Correr con:
    pytest scripts/test_procesamiento.py
"""
import re
from pathlib import Path

import pandas as pd
import pytest

from build_coefficients_comparison import OUTPUT_PATH as APORTE_PATH
from build_comparativo_provincias import build_comparativo, participaciones_anuales
from build_dependencia_fiscal import base_calibrada_cordoba, build_ratio, calcular_sensibilidad
from calibracion_iaraf import IMPACTO_PROVINCIAS_IARAF, calibrar, contrastar_con_cordoba
from coeficientes_ley23548 import COEFICIENTES_COPARTICIPACION
from process_coparticipacion import (
    CONCEPTO_GANANCIAS_PRE_2018,
    OUTPUT_PATH as COPART_PATH,
    load_ipc_empalmado,
    load_ipc_ferreres_var_pct,
    load_ipc_promedio_anual,
    load_ron_por_concepto,
)


@pytest.fixture(scope="module")
def ipc():
    return load_ipc_empalmado().set_index("anio")["ipc_promedio_anual"]


@pytest.fixture(scope="module")
def dependencia():
    return build_ratio().set_index("anio")


def test_ipc_cubre_2003_2025_y_crece_todos_los_anios(ipc):
    assert list(ipc.index) == list(range(2003, 2026))
    assert (ipc.diff().dropna() > 0).all()


def test_ipc_2016_es_un_promedio_y_no_el_valor_de_diciembre(ipc):
    # El IPC oficial solo trae diciembre de 2016; usarlo como promedio sesga ~10%.
    diciembre_2016 = load_ipc_promedio_anual().set_index("anio").loc[2016, "ipc_promedio_anual"]
    assert ipc[2016] < diciembre_2016 * 0.95


def test_ipc_2016_reproduce_la_variacion_2017_de_la_fuente(ipc):
    _, var_tabla_b = load_ipc_ferreres_var_pct()
    assert ipc[2017] / ipc[2016] - 1 == pytest.approx(var_tabla_b[2017])


def test_serie_de_coparticipacion_tiene_24_jurisdicciones_por_23_anios():
    df = pd.read_csv(COPART_PATH)
    assert len(df) == 24 * 23
    assert df["monto_real_base2016"].notna().all()


def test_aporte_vs_recibo_compara_participaciones_que_suman_uno():
    df = pd.read_csv(APORTE_PATH)
    assert df["pct_coparticipacion_entre_provincias"].sum() == pytest.approx(1.0)
    assert df["pct_pbg_aporte"].sum() == pytest.approx(1.0)


def test_ratio_de_dependencia_usa_partes_del_mismo_total(dependencia):
    d = dependencia
    assert ((d["ratio_coparticipacion_recaudacion"] > 0) & (d["ratio_coparticipacion_recaudacion"] < 1)).all()
    assert (d["coparticipacion_pesos"] + d["recursos_propios_pesos"] <= d["recaudacion_total_pesos"]).all()


def test_nacion_y_provincia_registran_la_misma_coparticipacion_todos_los_anios(dependencia):
    # Dos fuentes independientes (Hacienda y Rentas de Córdoba) con la misma definición.
    # Si el archivo provincial estuviera en millones, la diferencia sería de seis órdenes
    # de magnitud; si faltara un concepto, de 10% o más.
    assert (dependencia["diferencia_ron_vs_provincia"].abs() < 0.02).all()


def test_bruto_y_neto_mas_financiamiento_educativo_son_el_mismo_concepto():
    # Hacienda informa el bruto en 2003-2005 y 2011, y el neto + Financiamiento Educativo
    # el resto de los años. Si fueran conceptos distintos, la participación de cada
    # jurisdicción saltaría al cambiar de uno a otro (con solo el neto, hasta 1,7 puntos).
    df = load_ron_por_concepto()
    ley_23548 = df[~df["impuesto"].isin(
        [CONCEPTO_GANANCIAS_PRE_2018, "consenso fiscal ley 27429 compensacion"]
    )]
    montos = ley_23548.pivot_table(index="anio", columns="provincia", values="monto", aggfunc="sum")
    participacion = montos.div(montos.sum(axis=1), axis=0)
    # Hasta 2015: después cambian el régimen de CABA y la detracción para la ANSES.
    assert participacion.loc[2003:2015].diff().abs().max().max() < 0.0025


def test_sin_compensacion_cada_jurisdiccion_recibe_su_coeficiente_legal():
    tabla = build_comparativo()
    diferencia = tabla["participacion_2025_sin_compensacion"] - tabla["coeficiente_legal_renormalizado"]
    assert (diferencia.abs() < 0.002).all()
    assert tabla["participacion_2025"].sum() == pytest.approx(1.0)


def test_poblacion_y_per_capita_son_consistentes():
    tabla = build_comparativo().set_index("provincia")
    assert tabla["poblacion_2022"].sum() == 45_892_285  # total del país, Censo 2022
    # El índice es la participación 2022 sobre la participación en la población, así que
    # el promedio ponderado por población tiene que dar exactamente 1.
    ponderado = (tabla["indice_per_capita_2022"] * tabla["poblacion_2022"]).sum() / tabla["poblacion_2022"].sum()
    assert ponderado == pytest.approx(1.0)
    participacion_2022 = participaciones_anuales().loc[2022]
    esperado = participacion_2022 / (tabla["poblacion_2022"] / tabla["poblacion_2022"].sum())
    assert (tabla["indice_per_capita_2022"] - esperado).abs().max() < 1e-9


def test_sensibilidad_es_el_shock_por_la_parte_proporcional_de_la_dependencia(dependencia):
    sens = calcular_sensibilidad(2025, [-0.10]).iloc[0]
    fila = dependencia.loc[2025]
    proporcional = fila["coparticipacion_pesos"] - fila["compensacion_consenso_fiscal_pesos"]
    esperado = -0.10 * proporcional / fila["recaudacion_total_pesos"]
    assert sens["impacto_pct_recaudacion_total_cordoba"] == pytest.approx(esperado)


def test_calibracion_lleva_la_base_a_precios_del_cuatrimestre():
    calibracion = calibrar()
    assert calibracion["ajuste_precios"] > 1
    assert -0.20 < calibracion["variacion_implicita"] < 0


def test_contraste_con_cordoba_compara_el_mismo_cuatrimestre():
    contraste = contrastar_con_cordoba()
    # La pérdida y la variación salen de la misma base: pérdida / variación = enero-abril de
    # 2025 a precios de 2026, que tiene que ser del orden de lo que cobró Córdoba (~$1,8
    # billones). Si se mezclaran meses o años, esa base quedaría muy lejos.
    base = contraste["perdida_observada_pesos"] / contraste["variacion_real_observada"]
    assert 1.5e12 < base < 2.2e12
    assert contraste["perdida_modelo_pesos"] == pytest.approx(
        IMPACTO_PROVINCIAS_IARAF * COEFICIENTES_COPARTICIPACION["Córdoba"] / sum(COEFICIENTES_COPARTICIPACION.values())
    )


def test_simulador_web_usa_los_datos_del_repositorio():
    # El HTML tiene las constantes escritas a mano: si cambian los datos, este test avisa.
    html = (Path(__file__).resolve().parent.parent / "docs" / "simulador" / "index.html").read_text(encoding="utf-8")

    def constante(nombre):
        return float(re.search(rf"var {nombre} = ([0-9.]+);", html).group(1))

    _base, coparticipacion, recaudacion_total = base_calibrada_cordoba(2025)
    fila = build_ratio().set_index("anio").loc[2025]
    proporcional = coparticipacion - fila["compensacion_consenso_fiscal_pesos"]
    assert constante("COPARTICIPACION_PROPORCIONAL_CORDOBA_2025") == pytest.approx(proporcional, rel=1e-9)
    assert constante("RECAUDACION_TOTAL_CORDOBA_2025") == pytest.approx(recaudacion_total, rel=1e-9)
    assert constante("COEF_CORDOBA") == pytest.approx(COEFICIENTES_COPARTICIPACION["Córdoba"])

    escenario = f"{calibrar()['variacion_implicita'] * 100:.1f}"
    assert f'value="{escenario}"' in html
    assert f'slider.value = "{escenario}"' in html
