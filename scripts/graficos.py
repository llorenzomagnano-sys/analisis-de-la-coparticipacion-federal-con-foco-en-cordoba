"""
Utilidades compartidas por los gráficos de los notebooks.

`guardar_con_fuente` agrega debajo de cada gráfico la nota "Fuente: elaboración propia en
base a ..." y lo guarda en output/figures/, así la fuente viaja con la imagen (README,
notebooks o donde se la use).
"""
import textwrap

INK_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"

# Fuentes que se repiten en varios gráficos.
HACIENDA = "la Secretaría de Hacienda de la Nación (transferencias a provincias)"
FERRERES = "Fundación Norte y Sur / O. J. Ferreres (precios 2003-2016)"


def guardar_con_fuente(fig, ruta, fuente: str) -> None:
    """Agrega la nota de fuente debajo del gráfico y lo guarda en `ruta`.

    La nota va por fuera de la figura (y < 0, alineada arriba) y `bbox_inches="tight"`
    agranda la imagen para incluirla, así nunca se superpone con ejes, etiquetas ni
    leyendas.
    """
    nota = f"Fuente: elaboración propia en base a datos de {fuente}."
    caracteres_por_linea = int(fig.get_figwidth() * 15)
    fig.text(
        0.01, -0.01, textwrap.fill(nota, caracteres_por_linea),
        ha="left", va="top", fontsize=8.5, color=INK_SECONDARY,
    )
    fig.savefig(ruta, dpi=300, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.15)
