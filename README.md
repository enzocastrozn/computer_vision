# Monitor del conductor: distracción y somnolencia

Miniproyecto de Visión Artificial (Máster en IA, UMU, 2026/27). Con dos cámaras interiores, una de
frente a la cara y otra de lado para la cabina, se analizan tres señales: qué hace el conductor con
las manos, hacia dónde mira y si cierra los ojos.
Al combinarlas en el tiempo, el sistema avisa de distracción o de somnolencia. Son los dos avisos
que la UE exige en los coches nuevos: el de somnolencia (DDAW, desde julio de 2024) y el de
distracción (ADDW, desde julio de 2026).

Por ahora el repositorio tiene lo necesario para la exposición: el plan, una demo inicial y un
script para sacar imágenes de los datasets.

## Instalación

Todos los comandos se ejecutan desde la raíz del repositorio (`computer_vision/`).

### 1. Entorno

Con uv (recomendado; no hace falta tener Python 3.12, uv lo descarga):

```bash
uv sync --locked
```

Sin uv (hace falta Python 3.12 instalado):

```bash
# Linux / macOS
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Windows (PowerShell)
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Con uv, todos los comandos de este README se escriben como `uv run python ...`. Sin uv, activa
antes el entorno y usa `python ...`. No mezcles las dos formas.

### 2. Datos

Los datos van en `data/`, que no se sube al repositorio. La estructura esperada está en
[data/README.md](data/README.md). Descarga cada dataset a mano:

- **State Farm Distracted Driver Detection** (Kaggle, ~4,3 GB):
  1. Inicia sesión en Kaggle y acepta las reglas en
     https://www.kaggle.com/competitions/state-farm-distracted-driver-detection/rules
  2. En la pestaña Data, "Download All", y descomprime en `data/statefarm/`. Debe quedar
     `data/statefarm/driver_imgs_list.csv` y `data/statefarm/imgs/train/c0 ... c9`.

  > Si prefieres `kagglehub` (`kagglehub.competition_download(...)`), los archivos se guardan en la
  > caché de `~/.cache/kagglehub/`. Hay que copiar o enlazar esa carpeta a `data/statefarm/`, porque
  > los scripts del repositorio buscan ahí.

- **MRL Eye Dataset** (~340 MB):
  1. Descarga http://mrl.cs.vsb.cz/data/eyedataset/mrlEyes_2018_01.zip
     (página del dataset: https://mrl.cs.vsb.cz/eyedataset.html).
  2. Descomprime en `data/mrl_eye/`, de forma que quede `data/mrl_eye/mrlEyes_2018_01/`.

- **DMD, Driver Monitoring Dataset de Vicomtech** (solo vídeo RGB; uso académico, CC BY-NC-ND 4.0):
  1. Entra en https://dmd.vicomtech.org/, sección DOWNLOAD, y rellena el formulario de
     "Distraction" (y el de "Drowsiness" para la somnolencia). Hay que ser mayor de 18 años.
  2. Llega por correo un README y un enlace por conductor, por ejemplo
     `dmd-dataset-distraction-gA-1.tar.gz` (grupo A, conductor 1, unos 5 GB). Los enlaces caducan
     a las 48 horas. Para empezar no hace falta bajar todos los conductores.
  3. Descomprime cada archivo dentro de `data/`:

     ```bash
     tar -xzf dmd-dataset-distraction-gA-1.tar.gz -C data
     ```

     Queda `data/dmd/gA/1/s1/...`: tres vídeos (face, body, hands), un mosaico con los tres
     sincronizados y un `.json` con las etiquetas de cada fotograma.

Comprueba que los datos están donde deben:

```bash
ls data/statefarm/imgs/train/        # c0 ... c9
ls data/mrl_eye/mrlEyes_2018_01/     # carpetas s0001, s0002, ...
ls data/dmd/gA/1/s1/                 # *_rgb_face.mp4, *_rgb_body.mp4, *_rgb_hands.mp4, *.json
```

### 3. Modelo de la cara de MediaPipe

Necesario para la demo y para el cálculo de ojos y mirada (~4 MB, va a `data/models/`):

```bash
uv run python scripts/download_data.py
```

### 4. Ejecución

Demo con la webcam (`c` calibra la pose actual como "mirando a la carretera", `q` sale):

```bash
uv run python scripts/demo_webcam.py
uv run python scripts/demo_webcam.py --video clip.mp4 --guardar results/demo.mp4
```

Imágenes de los datasets para las diapositivas (van a `results/figuras/`, que sí está en el
repositorio):

```bash
uv run python scripts/figuras_dataset.py statefarm
uv run python scripts/figuras_dataset.py mrl
```

En la demo, el deslizador cambia el umbral del EAR.

### Problemas frecuentes

- **No encuentra el modelo de la cara**: falta el paso 3. Ejecuta `download_data.py`.
- **Falla `figuras_dataset.py`**: revisa que la carpeta del dataset tiene la estructura del paso 2.
- **La webcam no abre**: comprueba que ninguna otra aplicación la está usando.
- **`tar` falla**: el archivo puede estar incompleto o el enlace del DMD haber caducado; vuelve a
  descargarlo.
- **Falta el `.json` del DMD**: el paquete de distracción y el de somnolencia son archivos
  distintos; comprueba que descargaste el que necesitas.

## Plan

### Por qué dos cámaras

Una cámara de lado ve bien las manos, pero no la cara. Lo comprobamos con el detector de cara de
MediaPipe, el mismo de la demo:

| Imágenes | Cara detectada |
|---|---|
| State Farm (de lado), una foto por clase | 4 de 10, y solo cuando el conductor gira la cabeza hacia la cámara |
| DMD, cámara del cuerpo (de lado), 120 fotogramas de dos sesiones | 41 de 120 (34 %) |
| DMD, cámara de la cara (de frente), los mismos instantes | 116 de 120 (97 %) |

Por eso, como los sistemas de los coches reales, usamos una cámara de frente para ojos y mirada, y
otra de lado para las manos.

### Datos

- **State Farm Distracted Driver Detection (Kaggle):** 22.424 imágenes de 640×480 con 10 clases
  (conducción segura, móvil, bebe, radio...) de 26 conductores, vistas de lado. El test oficial no
  tiene etiquetas, así que train, validación y test salen de train **separando por conductor**.
- **MRL Eye Dataset:** 84.898 recortes de ojos en infrarrojo, abiertos o cerrados, de 37 sujetos.
  Se separan por sujeto.
- **DMD (Driver Monitoring Dataset, Vicomtech):** vídeo RGB de 1280×720 con tres cámaras
  sincronizadas (cara, cuerpo y manos) y etiquetas por fotograma: acción del conductor (casi las
  mismas clases que State Farm), si mira a la carretera, si habla y qué manos están en el volante.
  El paquete de somnolencia añade sus propias etiquetas. Se separa por conductor.
- **Grabaciones propias** (webcam o coche aparcado): solo para probar fuera de los datasets.

### Pipeline

| Parte | Preprocesado | Técnicas | BT |
|---|---|---|---|
| 1. Manos / actividad (10 clases; cámara de lado) | Redimensionar manteniendo 4:3 y normalizar como ImageNet. Augmentation: recorte y giro leves, brillo y contraste. Sin volteo horizontal (convertiría "móvil con la derecha" en "con la izquierda") | CNN propia, ResNet congelada frente a fine-tuning, ViT, DINOv2/v3 con un SVM (como proponen las orientaciones de la asignatura), Grad-CAM | 5a, 5b, 5c, 6a, 6b, 5h |
| 2. Ojos (cámara de frente) | Puntos de la cara con MediaPipe. Recortes: escala de grises, CLAHE para poca luz e infrarrojo, 64×64 | EAR (geométrico) frente a HOG+SVM y frente a una CNN sobre MRL Eye; PERCLOS | 6f, 3c, 4c, 5e |
| 3. Mirada (cámara de frente) | Los mismos puntos de MediaPipe | Pose de la cabeza con PnP sobre una cara 3D, con RANSAC frente a mínimos cuadrados cuando la mano tapa la cara | 2d, 7a, 7c |
| 4. Decisión | — | Ventana temporal: ojos cerrados más de 1 s, PERCLOS alto o mirada fuera más de 2 s, y entonces alerta | 6h, 1c |

Con las particiones por conductor y las semillas (BT1a) y las gráficas (BT1b), la suma es de
~100 %, el mínimo que exige el enunciado.

### Evaluación

- Accuracy, F1 macro y matriz de confusión.
- El mismo modelo con partición aleatoria frente a por conductor: con la aleatoria el acierto sale
  inflado (data leakage).
- Acierto de ojo abierto o cerrado por sujeto en MRL Eye.
- Mirada: el giro de la cabeza frente a la etiqueta "mira a la carretera" del DMD.
- Actividad en otro coche: el modelo entrenado con State Farm, probado con la cámara de lado del
  DMD (otros conductores y otro coche), con las clases que tienen en común.
- Somnolencia: las alertas frente a las etiquetas del paquete de somnolencia del DMD.
- Cuánto cae el acierto con nuestras grabaciones, y los fps en un portátil.

### Riesgos

- El DMD es grande (unos 5 GB por conductor): empezamos con pocos conductores y uno de cada 10-15
  fotogramas, que los seguidos son casi iguales.
- Las tres cámaras del DMD no empezaron a grabar a la vez y las etiquetas siguen el tiempo del
  mosaico: para sacar fotogramas alineados usamos la herramienta DEx de Vicomtech
  (https://github.com/Vicomtech/DMD-Driver-Monitoring-Dataset).
- Las clases de State Farm y del DMD no coinciden del todo: se comparan solo las comunes.
- Poca luz y gafas: los ojos se ven peor (CLAHE, y comparar con el infrarrojo de MRL Eye).

## Entorno (uv): reglas para el equipo

- `uv sync --locked` después de cada `git pull`.
- Para añadir o quitar librerías, `uv add` o `uv remove`, nunca `pip install`.
- Si cambian las librerías, regenera `requirements.txt` y súbelo en el mismo commit que
  `pyproject.toml` y `uv.lock`:
  `uv export --format requirements-txt --no-hashes --no-dev -o requirements.txt`

Igual que en el repositorio de Machine Learning: Python 3.12 y las versiones exactas en `uv.lock`.

## Datos y privacidad

`data/` no se sube (ver [data/README.md](data/README.md)): las licencias no permiten
redistribuir los datasets y las grabaciones propias son datos biométricos. `results/` sí se sube:
solo tiene figuras pequeñas. No guardéis ahí capturas ni vídeos con vuestras caras (los vídeos ya
están en `.gitignore`), ni fotogramas sacados del DMD: su licencia (CC BY-NC-ND) no permite
publicar material derivado. La única imagen del DMD en el repositorio es la figura oficial de sus
tres cámaras (`results/figuras/dmd_camaras.png`), sin modificar y citando la fuente.

Para las reglas que siguen los agentes de IA que trabajen en el repositorio, ver
[AGENTS.md](AGENTS.md).

## Uso de herramientas de IA

Los scripts y este plan se prepararon con ayuda de Claude Code (Anthropic). Hay que citarlo en la
memoria: el enunciado permite usar IA siempre que se cite.