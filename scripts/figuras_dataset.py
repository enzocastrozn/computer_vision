"""Imágenes de los datasets para las diapositivas.

    uv run python scripts/figuras_dataset.py statefarm   # una imagen de cada una de las 10 clases
    uv run python scripts/figuras_dataset.py mrl         # ojos abiertos y cerrados

Se guardan en results/figuras/, que sí se sube al repositorio (las usa la presentación).
"""

import argparse
import random
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SALIDA = ROOT / "results" / "figuras"

CLASES = {
    "c0": "Conducción segura",
    "c1": "Escribe con el móvil (dcha.)",
    "c2": "Habla por el móvil (dcha.)",
    "c3": "Escribe con el móvil (izda.)",
    "c4": "Habla por el móvil (izda.)",
    "c5": "Manipula la radio",
    "c6": "Bebe",
    "c7": "Alcanza algo detrás",
    "c8": "Se peina o maquilla",
    "c9": "Habla con el copiloto",
}


def rejilla(imagenes, titulos, columnas, salida, tam=(3.2, 2.6), gris=False, letra=14):
    filas = -(-len(imagenes) // columnas)
    fig, ejes = plt.subplots(filas, columnas, figsize=(tam[0] * columnas, tam[1] * filas), squeeze=False)
    for eje in ejes.ravel():
        eje.axis("off")
    for eje, imagen, titulo in zip(ejes.ravel(), imagenes, titulos):
        eje.imshow(imagen, cmap="gray" if gris else None)
        eje.set_title(titulo, fontsize=letra)  # grande: la figura se ve reducida en la diapositiva
    fig.tight_layout()
    fig.savefig(salida, dpi=150)
    plt.close(fig)
    print(f"Guardada {salida}")


def statefarm(raiz):
    df = pd.read_csv(raiz / "driver_imgs_list.csv")
    print(f"{len(df)} imágenes, {df['subject'].nunique()} conductores")
    print(df["classname"].value_counts().sort_index().to_string())
    imagenes, titulos = [], []
    for clase, nombre in CLASES.items():
        fila = df[df["classname"] == clase].sample(1, random_state=0).iloc[0]
        imagenes.append(Image.open(raiz / "imgs" / "train" / clase / fila["img"]).convert("RGB"))
        titulos.append(f"{clase}: {nombre}")
    rejilla(imagenes, titulos, 5, SALIDA / "statefarm_clases.png", tam=(4.0, 3.4))


def mrl(raiz, por_clase=8):
    # Nombre: sujeto_imagen_género_gafas_ESTADO_reflejos_luz_sensor.png (estado: 0 cerrado, 1 abierto)
    ficheros = sorted(raiz.rglob("s*_*.png"))
    abiertos = [f for f in ficheros if f.stem.split("_")[4] == "1"]
    cerrados = [f for f in ficheros if f.stem.split("_")[4] == "0"]
    print(f"{len(ficheros)} imágenes: {len(abiertos)} abiertos, {len(cerrados)} cerrados")
    random.seed(0)
    elegidos = random.sample(abiertos, por_clase) + random.sample(cerrados, por_clase)
    titulos = ["abierto"] * por_clase + ["cerrado"] * por_clase
    imagenes = [Image.open(f).convert("L") for f in elegidos]
    rejilla(imagenes, titulos, por_clase, SALIDA / "mrl_ojos.png", tam=(1.8, 2.1), gris=True, letra=15)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dataset", choices=["statefarm", "mrl"])
    ap.add_argument("--raiz", help="carpeta del dataset (por defecto data/statefarm o data/mrl_eye)")
    args = ap.parse_args()
    SALIDA.mkdir(parents=True, exist_ok=True)
    if args.dataset == "statefarm":
        statefarm(Path(args.raiz) if args.raiz else ROOT / "data" / "statefarm")
    else:
        mrl(Path(args.raiz) if args.raiz else ROOT / "data" / "mrl_eye")


if __name__ == "__main__":
    main()
