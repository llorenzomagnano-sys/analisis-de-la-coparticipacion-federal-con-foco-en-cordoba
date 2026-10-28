"""
Núcleo 3 — Calibración del escenario de referencia con la cifra pública de IARAF.

IARAF informó que en el primer cuatrimestre de 2026 la recaudación tributaria nacional
cayó en términos reales unos $5,1 billones, y que $1,4 billones de esa caída fueron
menos coparticipación para las provincias. Esta calibración busca la variación % de la
masa coparticipable que, con los coeficientes de la Ley 23.548, reproduce esos $1,4
billones.

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

Lo que la calibración NO valida: el impacto en pesos sobre cada provincia sale
directamente de los $1,4 billones repartidos por coeficiente, así que no depende de la
masa estimada. La única cifra que depende de esa estimación es la variación %
implícita, y no hay en el repositorio una serie independiente de masa coparticipable
2026 contra la cual contrastarla.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))
from build_comparativo_provincias import compensacion_consenso_fiscal  # noqa: E402
from coeficientes_ley23548 import COEFICIENTES_COPARTICIPACION  # noqa: E402
from process_coparticipacion import load_ipc_nacional_mensual  # noqa: E402

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


if __name__ == "__main__":
    for clave, valor in calibrar().items():
        print(f"{clave}: {valor:,.4f}")
