# Mini-JARVIS — Asistente de voz inteligente (versión NUBE)
Proyecto Integrador | Redes Neuronales | CENESTUR

## Descripción
Misma arquitectura que la versión local, pero el LLM corre en la nube
a través de la API de **Groq** en vez de un modelo local con Ollama.
El STT (Whisper) y el TTS siguen corriendo en tu computadora.

## Modos de uso
- 🎤 **Por voz:** presiona ENTER y habla por el micrófono
- ⌨️ **Por texto:** escribe tu pregunta directamente
- 🔊 **Salida:** la respuesta siempre se reproduce por voz

## Estructura del proyecto
```
Mini-Jarvis-nube/
├── Asistente.py         → asistente completo (voz y texto, LLM vía Groq)
├── exploracion.py        → módulo de exploración del modelo (igual que la versión local)
├── Requerimientos.txt     → dependencias
├── .gitignore
├── Readme.md
└── ffmpeg.exe
```

## Instalación
```bash
pip install -r Requerimientos.txt
```
Necesitas una cuenta de **Groq** con tu propia API key (gratis) y un archivo
`.env` con esa clave. Ver la sección "Cómo conseguir la API key" más abajo.

Y **ffmpeg** instalado en el sistema (o su ejecutable disponible en el PATH,
como el `ffmpeg.exe` que ya está en esta carpeta) para que Whisper pueda
procesar el audio.

## Cómo conseguir la API key de Groq
1. Entra a **https://console.groq.com** y crea una cuenta (es gratis).
2. En el panel, busca la sección **"API Keys"** y crea una nueva (empieza con `gsk_...`).
3. Copia esa clave.
4. En esta misma carpeta (`Mini-Jarvis-nube/`), crea un archivo llamado
   exactamente `.env` (sin nombre antes del punto) con esta línea adentro:
   ```
   GROQ_API_KEY="gsk_tu_clave_aqui"
   ```
5. Ese archivo nunca se sube a GitHub porque ya está en el `.gitignore`.

## Ejecución
```bash
# Asistente de voz y texto (Groq)
python Asistente.py

# Exploración de la arquitectura Transformer
python exploracion.py
```

## Proceso interno del modelo (identificación)
1. **Tokenización**: el texto se divide en tokens (~30-50 según el idioma).
2. **Embedding**: cada token se convierte en un vector de alta dimensión.
3. **Atención + feed-forward**: cada token "mira" a todos los demás para
   construir una representación contextual.
4. **Actualización por contexto**: cada capa refina el significado del token.
5. **Predicción con softmax**: se calcula la probabilidad del siguiente token.
6. **Repetición**: el proceso se repite hasta terminar la respuesta.

Ver `exploracion.py` para la demostración con una frase de ejemplo real.

## Limitaciones conocidas
- Alucinaciones (puede inventar información).
- Dificultad con razonamiento matemático exacto.
- Pérdida de contexto en conversaciones muy largas.
- Sesgos heredados del corpus de entrenamiento.
- No tiene memoria real fuera del contexto de la conversación actual.
- Depende de conexión a internet (a diferencia de la versión local con Ollama).
