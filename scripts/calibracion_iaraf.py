"""
Núcleo 3 — Calibración del escenario de referencia con la cifra pública de IARAF.

IARAF informó que en el primer cuatrimestre de 2026 la recaudación tributaria nacional
cayó un 6,7% real interanual, unos $5,1 billones (FUENTE_IARAF). De esa caída, $1,4
billones habrían sido menos coparticipación para las provincias; esa cifra no está en el
resumen publicado en la web de IARAF sino, según la prensa, en el informe completo (un
PDF en Google Drive que no pude abrir), así que no está verificada contra el original.
Esta calibración busca la variación % de la masa coparticipable que, con los
coeficientes de la Ley 23.548, reproduce esos $1,4 billones. El modelo es lineal: con
otra cifra de impacto, la variación y el impacto por provincia escalan en proporción.

Cómo se arma la masa coparticipable de referencia para el cuatrimestre:

  1. Coparticipación que recibieron las 24 jurisdicciones en 2025 (Núcleo 1), sin la
     compensación del Consenso Fiscal: es un monto fijo por provincia y no sigue los
     coeficientes del simulador.
  2. Un cuatrimestre = 4/12 del año (aproximación declarada; no hay datos mensuales de
     coparticipación en el repositorio).
  3. Llevada a precios de enero-abril de 2026 con el IPC nacional (promedio de esos
     cuatro meses contra el promedio de 2025). Sin este paso, la base quedaría en pesos
     de 2025 contra un shock medido en pesos de 2026, y la variación implícita saldría
     sobreestimada en la misma proporción.
  4. Dividida por la suma de los 24 coeficientes (~0,59) para pasar de lo que reciben
     las provincias a la masa total, que incluye la parte de Nación y del Fondo ATN.

El impacto en pesos sobre cada provincia sale directamente de los $1,4 billones
repartidos por coeficiente, así que no depende de la masa estimada; la variación %
implícita sí.

CONTRASTE (`contrastar_con_cordoba`): el archivo de Rentas de Córdoba del Núcleo 4 trae
lo que la provincia efectivamente cobró en enero-abril de 2026. Comparando cada mes con
el mismo mes de 2025 llevado a precios de 2026 con el IPC, se obtiene la variación real
y la pérdida en pesos que tuvo Córdoba, contra las que estima el modelo. Se usa la parte
de la coparticipación que sigue los coeficientes (sin la compensación ni el bono del
Consenso Fiscal), que es lo que el simulador mueve.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
from build_comparativo_provincias import compensacion_consenso_fiscal  # noqa: E402
from build_dependencia_fiscal import load_series_dgr_mensuales  # noqa: E402
from coeficientes_ley23548 import COEFICIENTES_COPARTICIPACION  # noqa: E402
from process_coparticipacion import load_ipc_nacional_mensual  # noqa: E402

FUENTE_IARAF = (
    "https://www.iaraf.org/index.php/13-areas-de-estudio/area-fiscal/723-informe-economico-2026-05-05"
)
IMPACTO_PROVINCIAS_IARAF = -1.4e12  # pesos, primer cuatrimestre de 2026
CAIDA_TOTAL_RECAUDACION_IARAF = -5.1e12  # pesos, primer cuatrimestre de 2026

ANIO_BASE = 2025
PERIODOS_CUATRIMESTRE = [202601, 202602, 202603, 202604]


def calibrar() -> dict:
    """Devuelve la masa coparticipable de referencia del cuatrimestre y la variación %
    que reproduce el impacto informado por IARAF, con los pasos intermedios."""
    suma_coeficientes = sum(COEFICIENTES_COPARTICIPACION.values())

    recibido_anio_base = compensacion_consenso_fiscal(ANIO_BASE)["sin_compensacion"].sum() * 1e6

    ipc = load_ipc_nacional_mensual().set_index("Periodo")["Indice_IPC"]
    periodos_base = [p for p in ipc.index if p // 100 == ANIO_BASE]
    faltantes = set(PERIODOS_CUATRIMESTRE) - set(ipc.index)
    if len(periodos_base) != 12 or faltantes:
        raise SystemExit("Falta IPC mensual para el año base o para el cuatrimestre; no se calibra con supuestos.")
    ajuste_precios = ipc.loc[PERIODOS_CUATRIMESTRE].mean() / ipc.loc[periodos_base].mean()

    recibido_cuatrimestre = recibido_anio_base * 4 / 12 * ajuste_precios
    recaudacion_base = recibido_cuatrimestre / suma_coeficientes
    variacion_implicita = IMPACTO_PROVINCIAS_IARAF / suma_coeficientes / recaudacion_base

    return {
        "suma_coeficientes": suma_coeficientes,
        "recibido_anio_base": recibido_anio_base,
        "ajuste_precios": ajuste_precios,
        "recibido_cuatrimestre": recibido_cuatrimestre,
        "recaudacion_base": recaudacion_base,
        "variacion_implicita": variacion_implicita,
    }


def contrastar_con_cordoba() -> dict:
    """Variación real y pérdida en pesos de la coparticipación proporcional de Córdoba en
    el cuatrimestre según el archivo de Rentas, contra lo que estima el modelo."""
    mensual = load_series_dgr_mensuales()
    proporcional = mensual["coparticipacion_pesos"] - mensual["compensacion_consenso_fiscal_pesos"]
    ipc = load_ipc_nacional_mensual().set_index("Periodo")["Indice_IPC"]

    periodos_previos = [p - 100 for p in PERIODOS_CUATRIMESTRE]
    necesarios = set(PERIODOS_CUATRIMESTRE + periodos_previos)
    faltantes = (necesarios - set(proporcional.index)) | (necesarios - set(ipc.index))
    if faltantes:
        raise SystemExit(f"Faltan datos de Córdoba o de IPC para {sorted(faltantes)}; no se contrasta.")

    observado = proporcional.loc[PERIODOS_CUATRIMESTRE].sum()
    previo_a_precios_actuales = sum(
        proporcional.loc[previo] * ipc.loc[actual] / ipc.loc[previo]
        for previo, actual in zip(periodos_previos, PERIODOS_CUATRIMESTRE)
    )

    coeficiente_cordoba = COEFICIENTES_COPARTICIPACION["Córdoba"]
    suma_coeficientes = sum(COEFICIENTES_COPARTICIPACION.values())
    return {
        "variacion_real_observada": observado / previo_a_precios_actuales - 1,
        "perdida_observada_pesos": observado - previo_a_precios_actuales,
        "variacion_modelo": calibrar()["variacion_implicita"],
        "perdida_modelo_pesos": IMPACTO_PROVINCIAS_IARAF * coeficiente_cordoba / suma_coeficientes,
    }


if __name__ == "__main__":
    for clave, valor in calibrar().items():
        print(f"{clave}: {valor:,.4f}")
    for clave, valor in contrastar_con_cordoba().items():
        print(f"{clave}: {valor:,.4f}")
