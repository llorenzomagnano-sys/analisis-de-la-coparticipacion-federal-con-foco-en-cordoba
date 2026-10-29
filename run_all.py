#!/usr/bin/env python3
"""
Corre el pipeline completo del proyecto de punta a punta, con un solo comando:

    python run_all.py

Pasos:
  1. Procesamiento (Núcleos 1, 2, 4 y 5): genera los CSV de data/processed/.
  2. Tests automáticos: simulador (Núcleo 3) y chequeos de consistencia de los datos
     procesados (IPC, definición de coparticipación, participaciones, ratio de
     dependencia).
  3. Regeneración de los 5 notebooks (ejecuta cada uno de punta a punta con
     `jupyter nbconvert`, lo que a su vez regenera todas las figuras de
     output/figures/).

Los datos crudos vienen versionados en data/raw/ (trazabilidad de cada fuente en
data/raw/README.md), así que no hace falta acceso a internet.

Requiere las dependencias de requirements.txt instaladas (`pip install -r
requirements.txt`).
"""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

PASOS_PROCESAMIENTO = [
    ("Núcleo 1 — procesar y deflactar la serie de coparticipación", "process_coparticipacion.py"),
    ("Núcleo 1 — coparticipación como % del PIB y por habitante", "build_coparticipacion_pib_poblacion.py"),
    ("Núcleo 2 — comparar aporte (PBG) vs. recibo (coparticipación)", "build_coefficients_comparison.py"),
    ("Núcleo 2 — retenciones atribuibles a Córdoba", "build_retenciones_cordoba.py"),
    ("Núcleo 4 — ratio de dependencia fiscal de Córdoba", "build_dependencia_fiscal.py"),
    ("Núcleo 4 — dependencia de las 24 jurisdicciones", "build_dependencia_provincias.py"),
    ("Núcleo 5 — comparación entre las 24 jurisdicciones", "build_comparativo_provincias.py"),
]

NOTEBOOKS = [
    "01_serie_historica.ipynb",
    "02_aporte_vs_recibo.ipynb",
    "03_simulador_sensibilidad.ipynb",
    "04_dependencia_fiscal_cordoba.ipynb",
    "05_comparacion_provincias.ipynb",
]


def run(descripcion: str, cmd: list[str], cwd: Path) -> None:
    print(f"\n{'=' * 70}\n{descripcion}\n{'=' * 70}")
    resultado = subprocess.run(cmd, cwd=cwd)
    if resultado.returncode != 0:
        sys.exit(
            f"\nFalló: {descripcion!r} (comando: {' '.join(cmd)}). "
            "Se corta el pipeline acá -- revisar el error de arriba antes de reintentar."
        )


def main() -> None:
    print("Pipeline del proyecto: procesamiento, tests y notebooks (datos de data/raw/).")

    for descripcion, script in PASOS_PROCESAMIENTO:
        run(descripcion, [sys.executable, script], cwd=SCRIPTS_DIR)

    run(
        "Tests: simulador (Núcleo 3) y consistencia del procesamiento (Núcleos 1, 2, 4 y 5)",
        [sys.executable, "-m", "pytest", "test_simulator.py", "test_procesamiento.py", "-v"],
        cwd=SCRIPTS_DIR,
    )

    for notebook in NOTEBOOKS:
        run(
            f"Regenerar notebook: {notebook}",
            ["jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
             "--ExecutePreprocessor.timeout=300", notebook],
            cwd=NOTEBOOKS_DIR,
        )

    print(f"\n{'=' * 70}\nPipeline completo. Salidas actualizadas en data/processed/, "
          f"output/figures/ y notebooks/.\n{'=' * 70}")


if __name__ == "__main__":
    main()
