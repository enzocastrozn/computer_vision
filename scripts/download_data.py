"""Descarga el modelo de la cara de MediaPipe que necesita la demo (~4 MB).

    uv run python scripts/download_data.py

Lo guarda en data/models/face_landmarker.task (data/ no se sube al repositorio).
Los datasets se descargan aparte: ver INSTALL.txt.
"""

import sys
import urllib.request
from pathlib import Path

DESTINO = Path(__file__).resolve().parents[1] / "data" / "models" / "face_landmarker.task"
URLS = [  # la primera es la que enlaza la documentación de MediaPipe; la segunda, de reserva
    "https://huggingface.co/litert-community/MediaPipe-FaceLandmarker/resolve/main/face_landmarker.task",
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
]


def main():
    if DESTINO.exists():
        print(f"Ya existe {DESTINO}")
        return
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    for url in URLS:
        try:
            urllib.request.urlretrieve(url, DESTINO)
            print(f"Descargado {DESTINO}")
            return
        except OSError as error:
            print(f"Falló {url}: {error}")
    sys.exit("No se pudo descargar el modelo")


if __name__ == "__main__":
    main()
