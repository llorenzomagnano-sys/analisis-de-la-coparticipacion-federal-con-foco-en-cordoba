"""
Genera un GIF animado que muestra el simulador interactivo del Núcleo 3
(`notebooks/03_simulador_sensibilidad.ipynb`) recorriendo varios escenarios de shock,
para tener una demo visual en el README sin depender de que alguien corra el notebook.

Diseño (siguiendo la skill de dataviz del proyecto): un "stat tile" animado, no una
sola barra a pantalla completa -- el número es el protagonista, con un meter fino como
contexto secundario de dónde cae el shock dentro de un rango fijo. Muestra el impacto
en dos unidades: pesos (delta absoluto) y % de la recaudación total de Córdoba
(Núcleo 4) -- la lectura relativa es la que realmente responde "qué tan grave
es esto para Córdoba".

No es parte del pipeline de datos (run_all.py no lo llama) -- es un asset de
presentación. Se puede regenerar corriendo este script directamente:

    python scripts/build_demo_gif.py

Salida:
  - output/figures/simulador_interactivo_demo.gif
"""
import io
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from simulator import simular_shock  # noqa: E402
from coeficientes_ley23548 import COEFICIENTES_COPARTICIPACION  # noqa: E402
from build_dependencia_fiscal import base_calibrada_cordoba  # noqa: E402
from calibracion_iaraf import calibrar  # noqa: E402

OUTPUT_PATH = BASE_DIR / "output" / "figures" / "simulador_interactivo_demo.gif"

COLOR_NEGATIVO = "#e34948"
COLOR_POSITIVO = "#2a78d6"
TRACK_COLOR = "#e1e0d9"     # mismo tono que el grid del resto del proyecto
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
SURFACE = "#fcfcfb"

RANGO_METER = 15  # el meter cubre -15% a +15%

# Recorrido del "arrastre del slider": 0 -> -15 -> +10 -> escenario de comienzos de 2026
# (calibrado con IARAF) -> 0. Se interpola entre estos puntos para que la animación se
# sienta fluida, no a saltos.
ESCENARIO_2026_PCT = round(calibrar()["variacion_implicita"] * 100, 1)
KEYFRAMES_PCT = [0, -15, 10, ESCENARIO_2026_PCT, 0]
PASOS_POR_TRAMO = 18


def variaciones_interpoladas() -> list[float]:
    secuencia = []
    for inicio, fin in zip(KEYFRAMES_PCT[:-1], KEYFRAMES_PCT[1:]):
        for paso in range(PASOS_POR_TRAMO):
            t = paso / PASOS_POR_TRAMO
            secuencia.append(inicio + (fin - inicio) * t)
    secuencia.append(KEYFRAMES_PCT[-1])
    return secuencia


def datos_base() -> tuple[float, float]:
    """(masa coparticipable calibrada 2025, recaudación total de Córdoba 2025), misma
    calibración que el indicador de sensibilidad del Núcleo 4."""
    recaudacion_base, _copart, recaudacion_total_2025 = base_calibrada_cordoba(2025)
    return recaudacion_base, recaudacion_total_2025


def _ar(texto: str) -> str:
    """Formato numérico argentino: punto para miles, coma para decimales."""
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def render_frame(variacion_pct: float, recaudacion_base: float, recaudacion_total: float) -> Image.Image:
    variacion = variacion_pct / 100
    resultado = simular_shock(variacion, recaudacion_base, COEFICIENTES_COPARTICIPACION)
    cordoba = next(p for p in resultado["por_provincia"] if p["provincia"] == "Córdoba")
    impacto_pesos = cordoba["impacto_pesos"]
    impacto_pct_recaudacion = impacto_pesos / recaudacion_total
    color = COLOR_NEGATIVO if impacto_pesos < 0 else COLOR_POSITIVO

    fig = plt.figure(figsize=(7.2, 4), dpi=130)
    fig.patch.set_facecolor(SURFACE)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Eyebrow -- qué se está simulando.
    ax.text(
        0.07, 0.88, "SIMULADOR DE SENSIBILIDAD · CÓRDOBA",
        fontsize=10, color=INK_MUTED, fontweight="bold", ha="left", va="center",
        family="sans-serif",
    )
    ax.text(
        0.07, 0.80, _ar(f"Shock de recaudación nacional coparticipable: {variacion_pct:+.1f}%"),
        fontsize=11, color=INK_SECONDARY, ha="left", va="center",
    )

    # Stat tile: el número grande es el impacto relativo (la pregunta que importa:
    # "qué tan grave es esto para Córdoba"), con el delta en pesos como contexto.
    ax.text(
        0.07, 0.58, _ar(f"{impacto_pct_recaudacion:+.2%}"), fontsize=44, color=color,
        fontweight="bold", ha="left", va="center", family="sans-serif",
    )
    ax.text(
        0.07, 0.40, "de la recaudación total de Córdoba (2025)",
        fontsize=10.5, color=INK_SECONDARY, ha="left", va="center",
    )
    ax.text(
        0.07, 0.32, _ar(f"{'−' if impacto_pesos < 0 else '+'}${abs(impacto_pesos) / 1e9:,.1f} mil millones de coparticipación"),
        fontsize=10.5, color=INK_MUTED, ha="left", va="center",
    )

    # Meter: dónde cae el shock dentro de un rango fijo -15%/+15% (mismo tono de grid
    # que el resto del proyecto para el track, marca fina con extremo redondeado).
    y_meter = 0.14
    x0, x1 = 0.07, 0.93
    centro = (x0 + x1) / 2
    escala = (x1 - x0) / (2 * RANGO_METER)

    ax.plot([x0, x1], [y_meter, y_meter], color=TRACK_COLOR, linewidth=10, solid_capstyle="round", zorder=1)
    x_valor = centro + max(min(variacion_pct, RANGO_METER), -RANGO_METER) * escala
    ax.plot([centro, x_valor], [y_meter, y_meter], color=color, linewidth=10, solid_capstyle="round", zorder=2)
    ax.plot([centro, centro], [y_meter - 0.035, y_meter + 0.035], color=SURFACE, linewidth=2, zorder=3)

    for pct_tick, x_tick, ha in [(-RANGO_METER, x0, "left"), (0, centro, "center"), (RANGO_METER, x1, "right")]:
        ax.text(x_tick, y_meter - 0.075, f"{pct_tick:+.0f}%".replace("+0%", "0%"), fontsize=8.5, color=INK_MUTED, ha=ha, va="top")

    fig.canvas.draw()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=SURFACE)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def main() -> None:
    recaudacion_base, recaudacion_total = datos_base()
    variaciones = variaciones_interpoladas()
    frames = [render_frame(v, recaudacion_base, recaudacion_total) for v in variaciones]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=45,
        loop=0,
    )
    print(f"Guardado: {OUTPUT_PATH} ({len(frames)} frames)")


if __name__ == "__main__":
    main()
