"""Demo con dos cámaras sobre una sesión del DMD: la cara analizada y las etiquetas del dataset.

    uv run python scripts/demo_dmd.py data/dmd/gA/1/s2
    uv run python scripts/demo_dmd.py data/dmd/gA/1/s2 --inicio 60 --fin 90 --guardar demo_dmd.mp4
    uv run python scripts/demo_dmd.py data/dmd/gA/1/s2 --sin-ventana    # solo la comparación final

Usa el vídeo mosaico del DMD, que ya trae las tres cámaras sincronizadas y tiene un fotograma por
cada fotograma anotado: arriba a la izquierda las manos, abajo a la izquierda la cara y abajo a la
derecha el cuerpo (de lado). Sobre la cámara de la cara aplica lo mismo que demo_webcam.py (EAR,
giro de la cabeza y avisos), y en el hueco de arriba a la derecha escribe la etiqueta del DMD
frente a lo que dice nuestro sistema. Al final compara nuestra "mirada fuera" con la etiqueta
"mira a la carretera" del DMD.

La pose "mirando a la carretera" se toma como la mediana de los primeros fotogramas que el DMD
etiqueta como mirando a la carretera. Con ventana, el vídeo va a velocidad real.
Teclas: espacio = pausa, q o Esc = salir.

Primer resultado (conductor gA/1, sesión s2 completa, 13.482 fotogramas comparados):
    umbral 30°: coincide en el 89,5 %, detecta el 34 % de los fotogramas en que NO mira la carretera
    umbral 20°: 92,5 % y 65 %   |   umbral 15°: 90,7 % y 81 %
    sesión s1 (conduciendo de verdad), 20°: 76,7 % y 90 %
El umbral está elegido con estos mismos datos: para la memoria hay que fijarlo con unos
conductores y medirlo con otros.

Ojo con la licencia del DMD (CC BY-NC-ND): el vídeo que se guarde es material derivado; se puede
enseñar en clase, pero no se sube al repositorio (los .mp4 ya están en .gitignore).
"""

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

import mediapipe as mp

from demo_webcam import (GIRO_MAXIMO, OJO_DERECHO, OJO_IZQUIERDO, SEGUNDOS_MIRADA_FUERA,
                         SEGUNDOS_OJOS_CERRADOS, ROOT, crear_detector, ear, giro_cabeza)

VENTANA = "Monitor del conductor - DMD"
UMBRAL_EAR = 0.20
FOTOGRAMAS_REFERENCIA = 60  # fotogramas "mirando a la carretera" para fijar la pose de referencia

NOMBRES = {  # etiquetas del DMD en español, para la pantalla
    "safe_drive": "conduccion segura", "texting_right": "escribe (dcha.)", "texting_left": "escribe (izda.)",
    "phonecall_right": "llama (dcha.)", "phonecall_left": "llama (izda.)", "radio": "radio",
    "drinking": "bebe", "reach_side": "alcanza a un lado", "reach_backseat": "alcanza atras",
    "hair_and_makeup": "se peina o maquilla", "talking_to_passenger": "habla con el copiloto",
    "change_gear": "cambia de marcha", "standstill_or_waiting": "parado", "unclassified": "sin clasificar",
}


def etiquetas_por_fotograma(ruta_json):
    """Lee el JSON (OpenLABEL) y devuelve, para cada nivel, un dict fotograma -> etiqueta."""
    datos = json.loads(Path(ruta_json).read_text(encoding="utf-8"))
    acciones = datos["openlabel"]["actions"]
    por_nivel = {}
    for accion in acciones.values():
        nivel, _, etiqueta = accion["type"].partition("/")
        for tramo in accion.get("frame_intervals", []):
            for f in range(tramo["frame_start"], tramo["frame_end"] + 1):
                por_nivel.setdefault(nivel, {})[f] = etiqueta
    return por_nivel


def escribir(imagen, linea, fila, color=(255, 255, 255), x=652):
    y = 32 + 30 * fila
    cv2.putText(imagen, linea, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2, cv2.LINE_AA)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sesion", help="carpeta de una sesión del DMD, p. ej. data/dmd/gA/1/s2")
    ap.add_argument("--inicio", type=float, default=0, help="segundo de inicio")
    ap.add_argument("--fin", type=float, help="segundo final")
    ap.add_argument("--guardar", help="guardar el vídeo anotado (.mp4); no subirlo al repositorio")
    ap.add_argument("--sin-ventana", action="store_true", help="procesar sin mostrar nada")
    ap.add_argument("--giro", type=float, default=20,
                    help=f"grados de giro a partir de los que la mirada cuenta como fuera (por defecto 20; "
                         f"la demo de la webcam usa {GIRO_MAXIMO})")
    ap.add_argument("--modelo", default=str(ROOT / "data" / "models" / "face_landmarker.task"))
    args = ap.parse_args()

    sesion = Path(args.sesion)
    mosaico = next(sesion.glob("*_rgb_mosaic.avi"))
    etiquetas = etiquetas_por_fotograma(next(sesion.glob("*_rgb_ann_*.json")))
    accion_dmd = etiquetas.get("driver_actions", {})
    mirada_dmd = etiquetas.get("gaze_on_road", {})

    cap = cv2.VideoCapture(str(mosaico))
    fps = cap.get(cv2.CAP_PROP_FPS) or 29.76
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    primero = int(args.inicio * fps)
    ultimo = min(total, int(args.fin * fps)) if args.fin else total
    cap.set(cv2.CAP_PROP_POS_FRAMES, primero)

    detector = crear_detector(args.modelo)
    escritor = None
    referencias, referencia = [], None
    cerrados_desde = fuera_desde = None
    cuenta = {"coinciden": 0, "total": 0, "fuera_dmd": 0, "fuera_dmd_detectado": 0}

    for n in range(primero, ultimo):
        inicio_fotograma = time.perf_counter()
        ok, imagen = cap.read()
        if not ok:
            break
        t = n / fps
        cara = np.ascontiguousarray(cv2.cvtColor(imagen[360:720, 0:640], cv2.COLOR_BGR2RGB))
        resultado = detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cara), int(t * 1000))
        imagen[0:360, 640:1280] = 0  # el hueco negro del mosaico pasa a ser nuestro panel
        mira_dmd = mirada_dmd.get(n)
        alertas, fuera = [], None

        if resultado.face_landmarks:
            puntos = np.array([(p.x * 640, p.y * 360 + 360) for p in resultado.face_landmarks[0]])
            valor = (ear(puntos[OJO_DERECHO]) + ear(puntos[OJO_IZQUIERDO])) / 2
            cerrado = valor < UMBRAL_EAR
            for i in OJO_DERECHO + OJO_IZQUIERDO:
                cv2.circle(imagen, tuple(int(c) for c in puntos[i]), 2, (0, 0, 255) if cerrado else (0, 255, 255), -1)
            lateral, cabeceo = giro_cabeza(resultado.facial_transformation_matrixes[0])

            if referencia is None:
                if mira_dmd == "looking_road":
                    referencias.append((lateral, cabeceo))
                if len(referencias) >= FOTOGRAMAS_REFERENCIA:
                    referencia = tuple(np.median(referencias, axis=0))
            if referencia is not None:
                lateral, cabeceo = lateral - referencia[0], cabeceo - referencia[1]
                fuera = abs(lateral) > args.giro or abs(cabeceo) > args.giro

            cerrados_desde = (cerrados_desde if cerrados_desde is not None else t) if cerrado else None
            fuera_desde = (fuera_desde if fuera_desde is not None else t) if fuera else None
            if cerrados_desde is not None and t - cerrados_desde >= SEGUNDOS_OJOS_CERRADOS:
                alertas.append("SOMNOLENCIA: ojos cerrados")
            if fuera_desde is not None and t - fuera_desde >= SEGUNDOS_MIRADA_FUERA:
                alertas.append("DISTRACCION: mirada fuera")
            escribir(imagen, f"Nuestro: EAR {valor:.2f}  giro {lateral:+.0f}  cabeceo {cabeceo:+.0f}", 3)
        else:
            cerrados_desde = fuera_desde = None
            escribir(imagen, "Nuestro: sin cara", 3, (0, 0, 255))

        # Comparación con la etiqueta del DMD (solo con la referencia ya fijada y la cara vista)
        if mira_dmd in ("looking_road", "not_looking_road") and fuera is not None:
            dmd_fuera = mira_dmd == "not_looking_road"
            cuenta["total"] += 1
            cuenta["coinciden"] += int(dmd_fuera == fuera)
            cuenta["fuera_dmd"] += int(dmd_fuera)
            cuenta["fuera_dmd_detectado"] += int(dmd_fuera and fuera)

        accion = NOMBRES.get(accion_dmd.get(n, ""), accion_dmd.get(n, "-"))
        escribir(imagen, f"t = {t:5.1f} s   fotograma {n}", 0, (180, 180, 180))
        escribir(imagen, f"DMD: {accion}", 1, (255, 200, 0))
        escribir(imagen, "DMD: " + {"looking_road": "mira la carretera", "not_looking_road": "NO mira la carretera"}.get(mira_dmd, "-"), 2, (255, 200, 0))
        if fuera is not None:
            escribir(imagen, "Nuestro: " + ("mirada FUERA" if fuera else "mira al frente"), 4)
        for k, alerta in enumerate(alertas):
            escribir(imagen, alerta, 6 + k, (0, 0, 255))
        if cuenta["total"]:
            escribir(imagen, f"Coincide con el DMD: {100 * cuenta['coinciden'] / cuenta['total']:.0f} %", 9, (0, 255, 0))

        if args.guardar:
            if escritor is None:
                Path(args.guardar).parent.mkdir(parents=True, exist_ok=True)
                escritor = cv2.VideoWriter(args.guardar, cv2.VideoWriter_fourcc(*"mp4v"), fps, (1280, 720))
            escritor.write(imagen)
        if not args.sin_ventana:
            cv2.imshow(VENTANA, imagen)
            # esperar lo que falte para ir a velocidad real (el análisis es más rápido que el vídeo)
            espera = max(1, int(1000 / fps - (time.perf_counter() - inicio_fotograma) * 1000))
            tecla = cv2.waitKey(espera) & 0xFF
            if tecla == ord(" "):
                tecla = cv2.waitKey(0) & 0xFF  # pausa hasta la siguiente tecla
            if tecla in (ord("q"), 27):
                break

    cap.release()
    if escritor:
        escritor.release()
    cv2.destroyAllWindows()
    if cuenta["total"]:
        print(f"Fotogramas comparados: {cuenta['total']}")
        print(f"Nuestra mirada coincide con la etiqueta del DMD en el {100 * cuenta['coinciden'] / cuenta['total']:.1f} %")
        if cuenta["fuera_dmd"]:
            print(f"De los fotogramas en que el DMD dice que NO mira la carretera, detectamos el "
                  f"{100 * cuenta['fuera_dmd_detectado'] / cuenta['fuera_dmd']:.1f} %")


if __name__ == "__main__":
    main()
