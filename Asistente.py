"""
DamJar — Versión en la nube (Backend)
Pipeline: Interfaz Web -> LLM (Groq) -> Respuesta
"""

print("[1/5] Cargando librerías...")
import os
import datetime
import threading
from flask import Flask, request, jsonify, send_from_directory
from groq import Groq
from dotenv import load_dotenv

print("[2/5] Configurando entorno...")
load_dotenv()

# ============================================================
# CONFIGURACIÓN DEL LLM (GROQ)
# ============================================================
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("ERROR: Falta GROQ_API_KEY en el archivo .env")
    input("Presiona Enter para salir...")
    exit(1)

MODEL = "openai/gpt-oss-20b"
MAX_TURNOS_MEMORIA = 5

SYSTEM_PROMPT = (
    "Eres DamJar, asistente de Damaris. Respondes cualquier pregunta del "
    "usuario de forma útil, corta, en español, "
    "pero puedes hablar de cualquier tema."
)

client = Groq(api_key=GROQ_API_KEY)
print("Groq configurado")

# ============================================================
# INICIO DEL SERVIDOR WEB
# ============================================================
print("[3/5] Iniciando servidor web...")
app = Flask(__name__, static_folder="App", static_url_path="")

# ============================================================
# FUNCIONES AUXILIARES — HORA, FECHA, TEMPORIZADOR
# ============================================================
PALABRAS_HORA = ["hora"]
PALABRAS_FECHA = ["día", "dia", "fecha"]
MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

def es_pregunta_de_hora(pregunta):
    pregunta = pregunta.lower()
    return any(p in pregunta for p in PALABRAS_HORA) or any(p in pregunta for p in PALABRAS_FECHA)

def _hora_en_formato_12(ahora):
    h = ahora.hour
    minuto = ahora.minute
    if h == 0:
        return f"12:{minuto:02d} de la madrugada"
    if h < 12:
        return f"{h}:{minuto:02d} de la mañana"
    if h == 12:
        return f"12:{minuto:02d} del mediodía"
    if h < 19:
        return f"{h - 12}:{minuto:02d} de la tarde"
    return f"{h - 12}:{minuto:02d} de la noche"

def responder_hora(pregunta):
    pregunta = pregunta.lower()
    pidio_hora = any(p in pregunta for p in PALABRAS_HORA)
    pidio_fecha = any(p in pregunta for p in PALABRAS_FECHA)
    ahora = datetime.datetime.now()
    dia_semana = DIAS_SEMANA[ahora.weekday()]
    mes = MESES[ahora.month - 1]
    hora_str = f"son las {_hora_en_formato_12(ahora)}"
    if pidio_fecha and pidio_hora:
        return f"Hoy es {dia_semana} {ahora.day} de {mes}, y {hora_str}."
    if pidio_fecha:
        return f"Hoy es {dia_semana} {ahora.day} de {mes}."
    return f"{hora_str.capitalize()}."

def es_pregunta_de_temporizador(pregunta):
    return "temporizador" in pregunta.lower()

def extraer_tiempo(pregunta):
    numero = None
    for palabra in pregunta.split():
        if palabra.isdigit():
            numero = int(palabra)
            break
    if numero is None:
        return None, None
    if "segundo" in pregunta.lower():
        return numero, "segundos"
    return numero, "minutos"

def iniciar_temporizador(cantidad, unidad):
    segundos_totales = cantidad if unidad == "segundos" else cantidad * 60
    def contar():
        restante = segundos_totales
        while restante > 0:
            mins, secs = divmod(restante, 60)
            print(f"[Temporizador] {mins:02d}:{secs:02d}")
            threading.Event().wait(1)
            restante -= 1
        print(f"Temporizador de {cantidad} {unidad} finalizado.")
    threading.Thread(target=contar, daemon=True).start()
    return f"Temporizador iniciado por {cantidad} {unidad}."

# ============================================================
# RUTA DE IMAGEN — OCR + RESUMEN
# ============================================================
@app.route("/imagen", methods=["POST"])
def procesar_imagen():
    try:
        from PIL import Image
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    except ImportError:
        return jsonify({"respuesta": "Falta instalar Pillow y pytesseract. Ejecuta: pip install pillow pytesseract"}), 501

    if "imagen" not in request.files:
        return jsonify({"respuesta": "No se recibió ninguna imagen."}), 400

    archivo = request.files["imagen"]
    if archivo.filename == "":
        return jsonify({"respuesta": "No se seleccionó ningún archivo."}), 400

    try:
        imagen = Image.open(archivo)
        texto_extraido = pytesseract.image_to_string(imagen, lang='spa+eng')
        
        if not texto_extraido.strip():
            return jsonify({"respuesta": "No pude leer texto en la imagen."})

        resumen_prompt = (
            "Aquí tienes el texto extraído de una imagen:\n\n"
            f"{texto_extraido}\n\n"
            "Haz un resumen claro y breve de este contenido en español."
        )

        mensajes = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": resumen_prompt}
        ]

        respuesta_ia = client.chat.completions.create(
            model=MODEL,
            messages=mensajes,
            temperature=0.5,
            max_tokens=400,
        )
        resumen = respuesta_ia.choices[0].message.content.strip()

        respuesta_final = f"Texto extraido:\n{texto_extraido[:500]}"
        if len(texto_extraido) > 500:
            respuesta_final += "..."
        respuesta_final += f"\n\nResumen:\n{resumen}"
        
        return jsonify({"respuesta": respuesta_final})

    except Exception as e:
        print(f"Error procesando imagen: {e}")
        return jsonify({"respuesta": f"Error al procesar la imagen: {str(e)}"}), 500

# ============================================================
# RUTAS DEL SERVIDOR
# ============================================================
@app.route("/")
def index():
    return send_from_directory("App", "app.html")

@app.route("/chat", methods=["POST"])
def chat():
    datos = request.get_json(force=True)
    pregunta = (datos.get("pregunta") or "").strip()
    historial_cliente = datos.get("historial", [])

    if not pregunta:
        return jsonify({"error": "No llegó ninguna pregunta"}), 400

    if es_pregunta_de_hora(pregunta):
        return jsonify({"respuesta": responder_hora(pregunta)})
    if es_pregunta_de_temporizador(pregunta):
        cantidad, unidad = extraer_tiempo(pregunta)
        if cantidad:
            mensaje = iniciar_temporizador(cantidad, unidad)
            return jsonify({"respuesta": mensaje})
        return jsonify({"respuesta": "¿De cuántos minutos o segundos quieres el temporizador?"})

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensajes += historial_cliente[-(MAX_TURNOS_MEMORIA * 2):]
    mensajes.append({"role": "user", "content": pregunta})

    try:
        respuesta = client.chat.completions.create(
            model=MODEL,
            messages=mensajes,
            temperature=0.7,
            max_tokens=300,
        )
        texto = respuesta.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error Groq: {e}")
        return jsonify({
            "respuesta": "Tuve un problema para pensar la respuesta, ¿puedes repetir la pregunta?"
        })

    if not texto:
        texto = "No se me ocurrió una respuesta clara, ¿puedes reformular la pregunta?"

    return jsonify({"respuesta": texto})

# ============================================================
# ARRANQUE DEL SERVIDOR
# ============================================================
print("[4/5] Servidor listo. Iniciando...")

if __name__ == "__main__":
    print("=== DAMJAR (NUBE) LISTO ===")
    print("Abre http://localhost:5000 en Google Chrome")
    try:
        app.run(debug=False, port=5000)
    except Exception as e:
        print(f"Error al iniciar el servidor: {e}")
        input("Presiona Enter para salir...")