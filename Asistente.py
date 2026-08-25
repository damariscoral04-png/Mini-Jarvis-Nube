# ==================================================
# MINI-JARVIS - Asistente de voz inteligente (VERSIÓN NUBE)
# Proyecto: Redes Neuronales | CENESTUR
# Pipeline: STT (Whisper) -> LLM (Groq, API en la nube) -> TTS (pyttsx3)
# ==================================================

import os
import numpy as np
import sounddevice as sd
import soundfile as sf
import whisper
import pyttsx3
from dotenv import load_dotenv
from groq import Groq

# ---------------- CONFIGURACIÓN ----------------
load_dotenv()  # carga la GROQ_API_KEY desde el archivo .env

SYSTEM_PROMPT = """Eres Mini-JARVIS, un asistente virtual inteligente, preciso y conciso.
Responde de forma clara, profesional y breve. Sé útil y directo."""

# openai/gpt-oss-20b: modelo recomendado por Groq, rápido y dentro
# del límite del plan gratuito.
MODELO_LLM = "openai/gpt-oss-20b"
TEMPERATURA = 0.7
MAX_TOKENS = 512
TURNOS_DE_MEMORIA = 3           # cuántos turnos (usuario+asistente) recuerda el asistente
DURACION_ESCUCHA = 5            # segundos que graba el micrófono por turno
AUDIO_TEMPORAL = "audio_temporal.wav"

# ---------------- CLIENTE GROQ ----------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("AVISO: no se encontró GROQ_API_KEY. Crea un archivo .env con:")
    print('GROQ_API_KEY="tu_api_key_aqui"')
cliente_groq = Groq(api_key=GROQ_API_KEY)

# ---------------- INICIALIZACIÓN ----------------
print("Cargando modelos, un momento...")
motor_voz = pyttsx3.init()
motor_voz.setProperty('rate', 150)
motor_voz.setProperty('volume', 0.9)
modelo_whisper = whisper.load_model("base")
historial_conversacion = []


def obtener_dispositivo_entrada():
    """
    Busca el micrófono a través del host API MME de Windows.
    El error 'could not create a primitive' suele venir de los host APIs
    DirectSound o WASAPI fallando al negociar el formato de audio con el
    driver. MME es más simple y compatible, así que se fuerza su uso en
    vez de dejar que Windows elija automáticamente.
    """
    try:
        for api in sd.query_hostapis():
            if api["name"] == "MME" and api["default_input_device"] != -1:
                return api["default_input_device"]
    except Exception:
        pass
    return None  # si no se encuentra MME, se deja que sounddevice use su default


DISPOSITIVO_ENTRADA = obtener_dispositivo_entrada()


def obtener_frecuencia_microfono():
    """
    Devuelve la frecuencia de muestreo nativa del micrófono (vía MME).
    Forzar una frecuencia fija (ej. 16000 Hz) puede fallar en Windows si
    el dispositivo no la soporta directamente. Whisper igual necesita
    16000 Hz, pero convierte el audio automáticamente al leer el archivo,
    así que grabamos a la frecuencia nativa y dejamos que Whisper haga
    esa conversión.
    """
    try:
        info = sd.query_devices(DISPOSITIVO_ENTRADA, kind="input")
        return int(info["default_samplerate"])
    except Exception:
        return 44100  # valor típico de respaldo si no se puede consultar


def verificar_microfono():
    """Detecta si hay un dispositivo de entrada de audio disponible.
    Esto ayuda a diagnosticar de entrada si un fallo del mic es de
    hardware/drivers y no del código."""
    try:
        dispositivo = sd.query_devices(DISPOSITIVO_ENTRADA, kind="input")
        print(f"Micrófono detectado: {dispositivo['name']} (host API: MME)")
        print(f"Frecuencia de grabación: {obtener_frecuencia_microfono()} Hz")
    except Exception as error:
        print("AVISO: no se detectó un micrófono de entrada por defecto.")
        print(f"Detalle: {error}")
        print("El modo de texto seguirá funcionando con normalidad.")


verificar_microfono()
print("Sistema listo.\n")


# ---------------- TTS: TEXTO -> VOZ ----------------
def hablar(texto):
    """Convierte la respuesta del LLM en voz y la reproduce por los parlantes."""
    print(f"Mini-JARVIS: {texto}")
    motor_voz.say(texto)
    motor_voz.runAndWait()


# ---------------- STT: VOZ -> TEXTO ----------------
def escuchar():
    """
    Graba audio del micrófono y lo transcribe a texto con Whisper.
    Si no logra reconocer nada (silencio, ruido, error de audio),
    devuelve una cadena vacía en vez de detener el programa.
    """
    print(f"\nEscuchando... habla ahora ({DURACION_ESCUCHA} segundos)")
    texto_reconocido = ""
    try:
        frecuencia = obtener_frecuencia_microfono()

        # Algunos drivers de audio en Windows rechazan la grabación en
        # mono (1 canal) y solo aceptan estéreo (2 canales). Se prueba
        # primero con 1 canal y, si falla, se reintenta con 2 antes de
        # rendirse.
        audio = None
        ultimo_error = None
        for canales in (1, 2):
            try:
                audio = sd.rec(
                    int(DURACION_ESCUCHA * frecuencia),
                    samplerate=frecuencia,
                    channels=canales,
                    dtype=np.float32,
                    device=DISPOSITIVO_ENTRADA,
                )
                sd.wait()
                break
            except Exception as error:
                ultimo_error = error
                audio = None

        if audio is None:
            raise ultimo_error

        sf.write(AUDIO_TEMPORAL, audio, frecuencia)

        # Whisper convierte automáticamente el audio del archivo a 16000 Hz,
        # sin importar a qué frecuencia o canales se haya grabado.
        resultado = modelo_whisper.transcribe(AUDIO_TEMPORAL, language="es", fp16=False)
        texto_reconocido = resultado["text"].strip()

    except Exception as error:
        print(f"Error capturando o transcribiendo audio: {error}")

    finally:
        if os.path.exists(AUDIO_TEMPORAL):
            os.remove(AUDIO_TEMPORAL)

    if texto_reconocido:
        print(f"Tú dijiste: {texto_reconocido}")
    return texto_reconocido


# ---------------- LLM: GENERAR RESPUESTA (GROQ) ----------------
def generar_respuesta(texto_usuario):
    """
    Envía el texto del usuario al LLM de Groq (API en la nube) junto con
    el historial reciente (memoria de conversación) y el system prompt
    que define la identidad del asistente. La explicación paso a paso de
    cómo procesa el texto el modelo (tokenización, embeddings, atención,
    softmax) está documentada y demostrada en exploracion.py.
    """
    global historial_conversacion
    historial_conversacion.append({"role": "user", "content": texto_usuario})

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensajes += historial_conversacion[-(TURNOS_DE_MEMORIA * 2):]

    try:
        respuesta = cliente_groq.chat.completions.create(
            model=MODELO_LLM,
            messages=mensajes,
            temperature=TEMPERATURA,
            max_tokens=MAX_TOKENS,
        )
        texto_respuesta = respuesta.choices[0].message.content
    except Exception as error:
        print(f"Error al llamar al LLM: {error}")
        texto_respuesta = "Tuve un problema para generar la respuesta. ¿Puedes repetir?"

    historial_conversacion.append({"role": "assistant", "content": texto_respuesta})
    return texto_respuesta


# ---------------- ORQUESTADOR PRINCIPAL ----------------
def main():
    print("=" * 55)
    print("MINI-JARVIS - Sistema de asistente (nube - Groq)")
    print("=" * 55)
    print("ENTER = hablar por el micrófono | escribe tu mensaje = modo texto")
    print("Escribe 'salir' para terminar.\n")

    hablar("Sistema listo. Soy Mini-JARVIS. ¿En qué puedo ayudarte?")

    while True:
        try:
            # Voz y texto son dos formas de entrada igual de válidas:
            # - Si el usuario solo presiona ENTER -> se activa el micrófono.
            # - Si el usuario escribe algo -> se usa eso directamente,
            #   sin pasar por el micrófono en absoluto.
            entrada = input("\n[ESPERANDO] ENTER para hablar, o escribe aquí: ")

            if entrada.strip() == "":
                print("[ESCUCHANDO]")
                texto_usuario = escuchar()

                # Si el micrófono no capturó nada, se reintenta el turno
                # (no se apaga el programa, y no se fuerza a usar texto)
                if not texto_usuario:
                    print("[ERROR] No se reconoció audio, intenta de nuevo.")
                    hablar("No te escuché bien, intenta de nuevo.")
                    continue
            else:
                texto_usuario = entrada.strip()

            if texto_usuario.lower() in ["salir", "terminar", "adiós", "adios"]:
                hablar("Hasta luego. Mini-JARVIS apagado.")
                break

            print("[PENSANDO]")
            respuesta = generar_respuesta(texto_usuario)

            print("[HABLANDO]")
            hablar(respuesta)

        except KeyboardInterrupt:
            hablar("Apagando sistema.")
            break
        except Exception as error:
            print(f"[ERROR] {error}")
            # Sin 'break': el asistente debe seguir funcionando
            continue


if __name__ == "__main__":
    main()
