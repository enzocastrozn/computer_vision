# Datos (no se suben al repositorio)

Esta carpeta está en `.gitignore`, salvo este fichero. Cómo descargar cada cosa: `INSTALL.txt`
(el modelo de MediaPipe con `scripts/download_data.py`; los datasets, a mano).

| Carpeta | Contenido | Condiciones |
|---|---|---|
| `statefarm/` | State Farm (Kaggle): `driver_imgs_list.csv` e `imgs/train/c0 ... c9` | Reglas de la competición; no redistribuir |
| `mrl_eye/` | MRL Eye: `mrlEyes_2018_01/s0001/s0001_00001_0_0_0_0_0_01.png ...` | Descarga pública; citar el dataset |
| `models/` | `face_landmarker.task` de MediaPipe | Apache 2.0 |
| `own/` | Grabaciones propias | Datos biométricos: solo el grupo, con consentimiento; no se publican |
