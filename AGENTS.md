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

## Uso de herramientas de IA

El enunciado permite usar IA «siempre citado y con comprensión de lo que se integra», y penaliza
el uso no reconocido. No hace falta registrar cada prompt: la memoria tendrá un apartado con las
herramientas usadas (nombre y modelo) y para qué se usó cada una.

- Al terminar una petición, di qué has generado (código, texto, figuras) para que la persona pueda
  citarlo y revisarlo.
- No copies contraseñas, tokens ni otros secretos en el código ni en los mensajes de commit.

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
- El uso de IA está permitido si se cita en la memoria (ver «Uso de herramientas de IA» arriba).
