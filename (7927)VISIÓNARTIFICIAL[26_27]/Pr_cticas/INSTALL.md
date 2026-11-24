# Instalación local de los notebooks

Esta es la guía canónica para ejecutar las prácticas en **Ubuntu o WSL con
Bash**. Se recomienda **Python 3.11** y un único entorno pyenv llamado
`va-master-notebooks`.

El entorno base sirve para los notebooks clásicos. Las dependencias pesadas se
añaden por familias solo cuando hacen falta: PyTorch/DINOv2, TensorFlow o YOLO.
No es necesario instalar todas para empezar la asignatura.

## 1. Dependencias del sistema

Ejecutar una sola vez:

```bash
sudo apt update
sudo apt install -y build-essential curl git make ffmpeg \
  libbz2-dev libffi-dev liblzma-dev libncursesw5-dev libreadline-dev \
  libsqlite3-dev libssl-dev libxml2-dev libxmlsec1-dev tk-dev xz-utils \
  zlib1g-dev
```

`build-essential` proporciona `gcc` y `make`, necesarios para el notebook 05.
El ejecutable `ffmpeg` se usa en los ejemplos de vídeo; el paquete Python
`ffmpeg-python` no lo sustituye.

## 2. Instalar y configurar pyenv

Si `pyenv --version` ya funciona, saltar este apartado.

```bash
curl -fsSL https://pyenv.run | bash

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
echo 'eval "$(pyenv init - bash)"' >> ~/.profile

exec "$SHELL"
```

Comprobar la instalación:

```bash
pyenv --version
```

## 3. Crear el entorno base

Desde `practicas/notebooks/`:

```bash
pyenv install -s 3.11
pyenv virtualenv 3.11 va-master-notebooks
pyenv activate va-master-notebooks

python -m pip install --upgrade pip
python -m pip install -r requirements-base.txt
python -m pip check
```

Si el entorno ya existe, no volver a crearlo. Basta con actualizar sus
dependencias declaradas:

```bash
pyenv activate va-master-notebooks
python -m pip install -r requirements-base.txt
python -m pip check
```

El entorno base cubre los notebooks 01–06: Jupyter, NumPy, SciPy, Matplotlib,
OpenCV, scikit-image, scikit-learn, Pillow, widgets y utilidades de vídeo.

## 4. Extra DINOv2/PyTorch para el notebook 07

`07_Ejemplos_uso_DINOv2.ipynb` necesita además:

- PyTorch y `torchvision`.
- `transformers`, para el ejemplo de profundidad.
- Conexión a Internet durante la primera ejecución para datos y modelos.

PyTorch se instala primero y por separado porque el paquete correcto depende
del hardware. Activar siempre el entorno antes de instalar:

```bash
pyenv activate va-master-notebooks
```

### Opción A: solo CPU

Es la opción más compatible. El notebook usa DINOv2 ViT-S/14 por defecto para
que pueda ejecutarse sin GPU, aunque será más lento.

```bash
python -m pip install torch torchvision \
  --index-url https://download.pytorch.org/whl/cpu
```

### Opción B: GPU NVIDIA en Ubuntu o WSL

Comprobar primero que la GPU es visible:

```bash
nvidia-smi
```

Después, abrir el [selector oficial de
PyTorch](https://pytorch.org/get-started/locally/) y elegir:

- **PyTorch Build:** Stable.
- **OS:** Linux.
- **Package:** Pip.
- **Language:** Python.
- **Compute Platform:** una versión CUDA compatible con el controlador mostrado
  por `nvidia-smi`.

Copiar y ejecutar el comando generado. Por ejemplo, si el selector recomienda
CUDA 12.6:

```bash
python -m pip install torch torchvision \
  --index-url https://download.pytorch.org/whl/cu126
```

No instalar manualmente el toolkit CUDA dentro del entorno: las ruedas de
PyTorch incluyen las bibliotecas de ejecución que necesitan. Sí hace falta un
controlador NVIDIA compatible en el sistema anfitrión.

### Instalar el resto del extra y verificarlo

Tras instalar PyTorch por una de las dos vías anteriores:

```bash
python -m pip install -r requirements-dinov2.txt
python -m pip check
```

Comprobar que Jupyter usará el intérprete correcto y que los imports funcionan:

```bash
python - <<'PY'
import sys
import torch
import torchvision
import transformers

print("Python:", sys.executable)
print("PyTorch:", torch.__version__)
print("torchvision:", torchvision.__version__)
print("Transformers:", transformers.__version__)
print("CUDA disponible:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
PY
```

Que `CUDA disponible` muestre `False` es correcto si se eligió la instalación
CPU. Si se pretendía usar NVIDIA y muestra `False`, revisar `nvidia-smi`, el
comando obtenido del selector y reiniciar el kernel de Jupyter tras instalar.

## 5. Extra TensorFlow/Keras para los notebooks 08 y 09

Se instala en el mismo entorno que el base y DINOv2. Incluye TensorFlow 2.21.0,
Keras 3.15.1 y TensorFlow Datasets 4.9.10. Ambos notebooks conservan los
entrenamientos originales y no instalan paquetes automáticamente en local.

### CPU

```bash
pyenv activate va-master-notebooks
python -m pip install -r requirements-tensorflow.txt
python -m pip check
```

### GPU NVIDIA en Ubuntu o WSL

Con un controlador compatible y `nvidia-smi` funcionando, añadir las dependencias
CUDA de la misma versión de TensorFlow:

```bash
pyenv activate va-master-notebooks
python -m pip install -r requirements-tensorflow.txt "tensorflow[and-cuda]==2.21.0"
python -m pip check
```

No instalar `tensorflow-cpu` junto con `tensorflow`: proporcionan el mismo módulo.
Si PyTorch ya está instalado, conservar su variante CPU/CUDA y comprobar que
`pip check` no encuentra conflictos. No ignorar conflictos ni reinstalar los
paquetes de NVIDIA con versiones arbitrarias. Véase la
[guía oficial de TensorFlow](https://www.tensorflow.org/install/pip).

Comprobar el intérprete, las versiones y los dispositivos:

```bash
python - <<'PY'
import sys
import tensorflow as tf
from tensorflow import keras
import tensorflow_datasets as tfds

print("Python:", sys.executable)
print("TensorFlow:", tf.__version__, "Keras:", keras.__version__, "TFDS:", tfds.__version__)
print("GPU:", tf.config.list_physical_devices("GPU"))
PY
```

Reiniciar el kernel si estaba abierto durante la instalación. En CPU, una lista
vacía de GPU es normal; los entrenamientos completos serán más lentos.

Las descargas se realizan una vez y se reutilizan, también al abrir los fuentes:

- 08: Fashion-MNIST, MNIST, flores y pesos preentrenados en `output/08_cnn/`.
  Entrena 10 + 5 + 10 épocas; el ajuste fino opcional de 40 sigue desactivado.
- 09: subconjunto ALOT de nueve clases (900 imágenes; descarga de unos 141 MiB)
  y checkpoint en `output/09_alot/`. Conserva los cuatro clasificadores clásicos
  y los entrenamientos de 10 + 30 épocas; la extracción Gabor se procesa por lotes.

```bash
make 08_VC_using_CNNs
make 09_ALOTexturesCNN
```

Ambos targets permiten hasta dos horas por celda para máquinas sin GPU.

Validación local (octubre de 2026, Python 3.11.11 y RTX 2080 Ti): 08 y 09
ejecutados completos sin errores, con 73 y 40 celdas de código, respectivamente.
Tiempos orientativos: tres y cuatro minutos. El extra no ha cambiado los
paquetes previos de DINOv2; pasan `pip check` y la prueba conjunta GPU
PyTorch/TensorFlow. En CPU se han probado el arranque y operaciones iniciales
de ambos notebooks, no los entrenamientos completos. Confirmada la ejecución completa
de ambos también en Colab.

## 6. Extra YOLO/ONNX para el notebook 10

Reutiliza PyTorch y `torchvision` instalados según el apartado 4, sin cambiar
su variante CPU/CUDA. En el mismo entorno:

```bash
python -m pip install -r requirements-yolo.txt
python -m pip check
make 10_YOLO_OD_ALOTextures
```

El extra fija Ultralytics headless y las herramientas ONNX. No instalar además
`ultralytics` ni su extra completo `export`: duplicarían OpenCV o añadirían
otros motores con restricciones innecesarias. Referencia:
[instalación oficial](https://docs.ultralytics.com/quickstart/).

El notebook conserva YOLOv8n, 300/200/100 imágenes y 10 épocas. Se recomienda
GPU; el target admite dos horas por celda en CPU. Todo queda en `output/10_yolo/`:
descargas y extracción reutilizables, dataset generado, configuración y `runs/`.
Reservar al menos 5 GiB: VisDrone ocupa unos 1,45 GiB comprimido. ALOT reutiliza
el archivo del 09 si existe. La comprobación AMP en GPU puede descargar pesos
auxiliares; el modelo de entrenamiento sigue siendo YOLOv8n.

Validado completo en local: 41 celdas sin errores, incluidas las 10 épocas,
carga del modelo docente, exportación ONNX e introspección con la imagen original.
El extra no ha alterado los paquetes previos y `pip check` pasa. Las pruebas
de inferencia/exportación en CPU también pasan. Confirmado también su funcionamiento en Colab.

## 7. Abrir Jupyter y ejecutar los notebooks

En cada sesión:

```bash
cd /ruta/al/repositorio/practicas/notebooks
pyenv activate va-master-notebooks
jupyter lab
```

Dentro de Jupyter, el kernel debe usar el mismo ejecutable mostrado por:

```bash
python -c 'import sys; print(sys.executable)'
```

También se puede validar un notebook desde la terminal. Por ejemplo:

```bash
make 06_HandEngineeredFeatures
make 07_Ejemplos_uso_DINOv2
```

`make` evalúa copias en `output/` y deja los notebooks fuente sin salidas. Si se
ejecuta un fuente directamente en Jupyter, limpiar sus salidas y contadores
antes de versionarlo con `jupyter nbconvert --clear-output --inplace nombre.ipynb`.

Las versiones ejecutadas, los datos descargados y otros artefactos se guardan
en `output/`, que está fuera de Git. `make clean` elimina esos resultados, pero
no los notebooks fuente ni el archivo histórico `old/`.

La primera ejecución del notebook 07 descarga:

- un subconjunto pequeño de imágenes;
- el código y los pesos de DINOv2 mediante PyTorch Hub;
- el modelo DPT-DINOv2 de profundidad mediante Hugging Face.

Las ejecuciones posteriores reutilizan las cachés de `output/`, PyTorch y
Hugging Face.

## 8. Google Colab

En Colab no hay que crear el entorno pyenv. PyTorch suele estar preinstalado y
se recomienda seleccionar un entorno con GPU para el notebook 07.

Si la celda inicial indica que falta `transformers`, instalarlo en una celda y
reiniciar el entorno de ejecución:

```python
%pip install "transformers>=4.40,<6"
```

Los notebooks no modifican automáticamente el entorno local del estudiante.

Para los notebooks 08 y 09 se recomienda igualmente un runtime con GPU. TensorFlow
suele estar preinstalado; si faltan dependencias, instalar el extra correspondiente
en ese runtime y reiniciarlo. Las versiones fijadas del extra son la referencia
de la instalación local con Python 3.11.

Los notebooks 06 a 10 están confirmados en Colab. En el 08, la celda
inicial instala únicamente `importlib-resources==7.1.0` si falta, para que TFDS
pueda preparar `tf_flowers`; no reinstala TensorFlow/Keras.

En el 10, el arranque instala solo los extras ausentes de Ultralytics y ONNX.
En Colab usa la variante normal de Ultralytics para reutilizar su OpenCV;
la variante headless de `requirements-yolo.txt` se reserva al entorno local.

## 9. Dependencias por familia

| Notebooks | Entorno necesario | Estado |
|---|---|---|
| 01–06 | `requirements-base.txt` | Disponible |
| 07 DINOv2 | PyTorch + `requirements-dinov2.txt` | Disponible |
| 08 CNNs y 09 ALOT | `requirements-tensorflow.txt` | Disponibles |
| 10 YOLO | PyTorch + `requirements-yolo.txt` | Disponible |

Los extras se instalan en el mismo entorno:

```bash
pyenv activate va-master-notebooks
python -m pip install -r requirements-NOMBRE.txt
python -m pip check
```

## 10. Problemas frecuentes

- **`ModuleNotFoundError` tras instalar:** comprobar `which python`,
  `python -m pip --version` y el kernel seleccionado en Jupyter; los tres deben
  corresponder a `va-master-notebooks`.
- **Jupyter estaba abierto durante la instalación:** reiniciar el kernel o
  cerrar y volver a abrir Jupyter Lab.
- **CUDA no aparece:** ejecutar `nvidia-smi` dentro de Ubuntu/WSL y comprobar
  que no se instaló por error la variante CPU de PyTorch.
- **Descargas lentas con pip:** consultar `SLOW_pip.md`.
- **Falta de espacio:** los modelos se almacenan normalmente en
  `~/.cache/torch/hub/` y `~/.cache/huggingface/`; los datos de los notebooks,
  en `output/`.
- **Problemas de paquetes:** ejecutar `python -m pip check` y conservar su
  salida completa para diagnosticar el conflicto.

