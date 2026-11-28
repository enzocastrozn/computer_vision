"""Demo inicial para la exposición: ojos (EAR) y giro de la cabeza con MediaPipe.

    uv run python scripts/download_data.py                 # una vez: descarga el modelo
    uv run python scripts/demo_webcam.py                   # webcam
    uv run python scripts/demo_webcam.py --video clip.mp4 --guardar results/demo.mp4

Teclas: c = tomar la pose actual como "mirando a la carretera", q o Esc = salir.
El deslizador cambia el umbral del EAR por debajo del cual el ojo cuenta como cerrado.
"""

import argparse
import math
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
VENTANA = "Monitor del conductor"

# Puntos de MediaPipe de cada ojo, en el orden del EAR (Soukupova y Cech, 2016):
# comisura, párpado superior x2, comisura, párpado inferior x2
OJO_DERECHO = [33, 160, 158, 133, 153, 144]
OJO_IZQUIERDO = [362, 385, 387, 263, 373, 380]

SEGUNDOS_OJOS_CERRADOS = 1.0  # ojos cerrados seguidos más de esto: alerta de somnolencia
SEGUNDOS_MIRADA_FUERA = 2.0  # cabeza girada más de esto: alerta de distracción
GIRO_MAXIMO = 30  # grados de giro (a los lados o arriba/abajo) respecto a la pose de referencia


def ear(puntos):
    """Eye aspect ratio: alto del ojo entre ancho. Baja casi a 0 al cerrar el ojo."""
    p = puntos[:, :2]
    alto = np.linalg.norm(p[1] - p[5]) + np.linalg.norm(p[2] - p[4])
    ancho = np.linalg.norm(p[0] - p[3])
    return alto / (2 * ancho) if ancho > 0 else 0.0


def giro_cabeza(matriz):
    """(giro lateral, cabeceo) en grados a partir de la matriz de pose que da MediaPipe."""
    R = np.asarray(matriz)[:3, :3]
    lateral = math.degrees(math.atan2(R[2, 0], math.hypot(R[2, 1], R[2, 2])))
    cabeceo = math.degrees(math.atan2(R[2, 1], R[2, 2]))
    return lateral, cabeceo


def crear_detector(modelo):
    opciones = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(modelo)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        output_facial_transformation_matrixes=True,
    )
    return mp.tasks.vision.FaceLandmarker.create_from_options(opciones)


def texto(imagen, linea, fila, color=(255, 255, 255)):
    cv2.putText(imagen, linea, (12, 30 + 28 * fila), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(imagen, linea, (12, 30 + 28 * fila), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--video", help="usar un vídeo en vez de la webcam")
    ap.add_argument("--camara", type=int, default=0, help="índice de la webcam")
    ap.add_argument("--guardar", help="guardar el vídeo con las anotaciones (.mp4)")
    ap.add_argument("--modelo", default=str(ROOT / "data" / "models" / "face_landmarker.task"))
    ap.add_argument("--sin-ventana", action="store_true", help="procesar sin mostrar nada (con --video)")
    args = ap.parse_args()

    if not Path(args.modelo).exists():
        raise SystemExit("Falta el modelo: uv run python scripts/download_data.py")
    cap = cv2.VideoCapture(args.video if args.video else args.camara)
    if not cap.isOpened():
        raise SystemExit("No se pudo abrir la cámara o el vídeo")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    if not args.sin_ventana:
        cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)
        cv2.createTrackbar("umbral EAR x100", VENTANA, 20, 50, lambda v: None)

    detector = crear_detector(args.modelo)
    escritor = None
    referencia = None  # (lateral, cabeceo) de la pose "mirando a la carretera"
    cerrados_desde = fuera_desde = None
    inicio, n = time.monotonic(), 0
    ultimo_ms = -1  # MediaPipe exige marcas de tiempo estrictamente crecientes

    while True:
        ok, imagen = cap.read()
        if not ok:
            break
        t = n / fps if args.video else time.monotonic() - inicio
        n += 1
        umbral = 0.20 if args.sin_ventana else cv2.getTrackbarPos("umbral EAR x100", VENTANA) / 100

        # La webcam puede entregar dos fotogramas en el mismo milisegundo: si la marca no avanza,
        # se le suma 1 ms para que MediaPipe no se pare con "timestamp must be monotonically increasing"
        ms = max(int(t * 1000), ultimo_ms + 1)
        ultimo_ms = ms

        rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        resultado = detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), ms)
        alertas = []
        if not resultado.face_landmarks:
            texto(imagen, "sin cara", 0, (0, 0, 255))
            cerrados_desde = fuera_desde = None
        else:
            h, w = imagen.shape[:2]
            puntos = np.array([(p.x * w, p.y * h) for p in resultado.face_landmarks[0]])
            valor = (ear(puntos[OJO_DERECHO]) + ear(puntos[OJO_IZQUIERDO])) / 2
            cerrado = valor < umbral
            for i in OJO_DERECHO + OJO_IZQUIERDO:
                cv2.circle(imagen, tuple(int(c) for c in puntos[i]), 2, (0, 0, 255) if cerrado else (0, 255, 255), -1)

            lateral, cabeceo = giro_cabeza(resultado.facial_transformation_matrixes[0])
            if referencia is None:
                referencia = (lateral, cabeceo)  # la primera pose vista cuenta como referencia
            lateral, cabeceo = lateral - referencia[0], cabeceo - referencia[1]
            fuera = abs(lateral) > GIRO_MAXIMO or abs(cabeceo) > GIRO_MAXIMO

            # Desde cuándo dura cada situación (None si no está pasando)
            if not cerrado:
                cerrados_desde = None
            elif cerrados_desde is None:
                cerrados_desde = t
            if not fuera:
                fuera_desde = None
            elif fuera_desde is None:
                fuera_desde = t
            if cerrados_desde is not None and t - cerrados_desde >= SEGUNDOS_OJOS_CERRADOS:
                alertas.append("SOMNOLENCIA: ojos cerrados")
            if fuera_desde is not None and t - fuera_desde >= SEGUNDOS_MIRADA_FUERA:
                alertas.append("DISTRACCION: mirada fuera")

            texto(imagen, f"EAR {valor:.2f} (umbral {umbral:.2f})", 0)
            texto(imagen, f"giro lateral {lateral:+.0f}  cabeceo {cabeceo:+.0f} grados", 1)
        for k, alerta in enumerate(alertas):
            texto(imagen, alerta, 3 + k, (0, 0, 255))

        if args.guardar:
            if escritor is None:
                Path(args.guardar).parent.mkdir(parents=True, exist_ok=True)
                h, w = imagen.shape[:2]
                escritor = cv2.VideoWriter(args.guardar, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
            escritor.write(imagen)
        if not args.sin_ventana:
            cv2.imshow(VENTANA, imagen)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), 27):
                break
            if tecla == ord("c"):
                referencia = None  # se toma la del siguiente fotograma

    cap.release()
    if escritor:
        escritor.release()
    cv2.destroyAllWindows()
    print(f"{n} fotogramas procesados")


if __name__ == "__main__":
    main()
