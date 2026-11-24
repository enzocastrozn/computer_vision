# AGENTS.md

Instrucciones para cualquier agente de IA que trabaje en este repositorio (GitHub Copilot, Claude
Code u otros). Responde en español. Los términos técnicos habituales se pueden dejar en inglés.

## Propósito del proyecto

Miniproyecto de Visión Artificial del Máster en Inteligencia Artificial de la Universidad de
Murcia (curso 2026/2027): un monitor del conductor que detecta distracción y somnolencia desde una
cámara interior. El plan (datos, preprocesado, técnicas y tópicos BT) está en [README.md](README.md).

Mantén el código mínimo y fácil de explicar: todo el grupo tiene que poder entenderlo. Los tópicos
BT1-BT7 usados tienen que sumar al menos un 100 %, y se valora más la justificación que la
cantidad de técnicas.

## Registro obligatorio de prompts

El enunciado penaliza el uso de IA no reconocido, así que **este registro es obligatorio en cada
petición**. Cómo funciona: [docs/ia/GUIA_REGISTRO_IA.md](docs/ia/GUIA_REGISTRO_IA.md).

1. **Identifica a la persona** con `git config user.name` y usa su archivo:

   | Si el nombre o el correo de git contiene | Archivo |
   |---|---|
   | `pablo` | `docs/ia/registro_ia_pablo.md` |
   | `enzo` | `docs/ia/registro_ia_enzo.md` |
   | `rodri` | `docs/ia/registro_ia_rodrigo.md` |

   Si no coincide con nadie, pregunta a quién corresponde el registro.
2. **Al empezar a trabajar en una petición,** lee el final del archivo. Si la última entrada ya contiene ese prompt con `Captura: automática (hook)`, la herramienta lo está registrando sola y no debes añadir nada. Si no, añade una entrada al final con la [plantilla](docs/ia/GUIA_REGISTRO_IA.md#plantilla-de-una-entrada) y copia el prompt **literalmente**, sin resumirlo ni corregirlo.
3. **Al terminar, si has creado tú la entrada,** complétala con el modelo y la versión que estés usando y con tu mensaje final. Si no sabes el modelo, escribe `no disponible`: no lo deduzcas.
4. **Deja `Análisis crítico` como pendiente.** Solo lo rellena la persona: no inventes qué se aceptó o se rechazó.
5. No edites entradas anteriores ni registros de otros miembros, y no copies contraseñas, tokens ni otros secretos.
6. Si tu modo de trabajo no permite editar archivos, recuérdale a la persona que copie el prompt y la respuesta a mano.

## Entorno

- Python **3.12** y **uv** para todo el grupo. Las dependencias están en `pyproject.toml` y `uv.lock`.
- Para añadir o quitar librerías, usa `uv add` o `uv remove`, nunca `pip install` ni `uv pip install`.
  No edites `uv.lock` a mano.
- Cada vez que cambien las librerías, regenera `requirements.txt` y súbelo en el mismo commit que
  `pyproject.toml` y `uv.lock`:

  ```bash
  uv export --format requirements-txt --no-hashes --no-dev -o requirements.txt
  ```

- Ejecuta con `uv run` o con el `.venv` del proyecto.

## Datos

- No subas al repositorio datasets, modelos descargados ni vídeos: `data/` está en `.gitignore`.
  `results/` sí se sube, pero solo con figuras pequeñas y sin caras del grupo.
- El uso de IA está permitido si se cita en la memoria (ver el registro de prompts arriba).
