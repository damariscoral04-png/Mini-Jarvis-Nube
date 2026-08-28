# DamJar — versión en la nube (Groq)

Versión web del asistente, pensada como complemento de la versión local
de escritorio. Usa el mismo concepto (personalidad, memoria de
conversación) pero con un LLM en la nube (Groq) en vez de local, y
captura/reproduce voz **en vivo** directamente en el navegador (Web
Speech API), sin grabar audio a un archivo ni instalar Vosk/pyttsx3.

## Estructura del proyecto
```
Mini-jarvis-nube/
├── Asistente.py           → backend: sirve la página y habla con Groq
├── Packages.txt            → dependencias de Python
├── .env                    → tu API key de Groq (no se sube a GitHub)
└── App/
    ├── app.html             → la página en sí
    ├── css/
    │   └── app.css          → estilos
    └── js/
        └── app.js           → micrófono en vivo, voz, memoria de conversación
```

## Por qué es más liviana que la versión local
No necesita: Ollama, modelo de Vosk, Tesseract, ni las librerías pesadas
como `torch`/`transformers`. Solo un servidor chico en Python que le
pasa el texto a Groq, y el navegador se encarga de todo el audio.

## Instalación

1. Instala las dependencias:
   ```
   pip install -r Packages.txt
   ```
2. Consigue tu API key gratis en https://console.groq.com (sección "API Keys").
3. Abre tu archivo `.env` y pon ahí tu API key:
   ```
   GROQ_API_KEY=tu_key_real_aqui
   ```
   (El archivo `.env` **no** debe subirse a GitHub — agrégalo al `.gitignore`.)

## Ejecutarlo
```
python Asistente.py
```
Abre en el navegador (usa **Google Chrome**, es el que mejor soporta la
Web Speech API): http://localhost:5000

## Cómo se usa
- Presiona el botón del micrófono 🎤 y habla — te escucha en vivo, sin
  límite de segundos fijo, y responde por voz automáticamente.
- O escribe tu pregunta en la caja de texto de abajo.

## Diferencias con la versión local
| | Local (`Mini-Jarvis-vc/Asistente.py`) | Nube (esta versión) |
|---|---|---|
| LLM | Ollama (`llama3.2:1b`), local | Groq (`llama-3.1-8b-instant`), en la nube |
| STT | Vosk, graba 8-10 seg fijos | Web Speech API del navegador, en vivo |
| TTS | pyttsx3 | Voz nativa del navegador |
| Requiere internet | No (excepto para OCR de imágenes) | Sí, siempre (LLM en la nube) |
| Funciones extra (hora, temporizador, imagen) | Sí | Aún no (versión MVP) |

## Nota de seguridad
La API key de Groq nunca se escribe en el código ni se manda al
navegador — vive solo en el archivo `.env` del servidor, y el frontend
solo habla con este mismo backend (`/chat`), nunca directo con Groq.