const micBtn = document.getElementById("micBtn");
const estadoDiv = document.getElementById("estado");
const chatDiv = document.getElementById("chat");
const cajaTexto = document.getElementById("cajaTexto");
const enviarBtn = document.getElementById("enviarBtn");
const cajaImagen = document.getElementById("cajaImagen");

let historial = [];
let temporizadorActivo = false;
let temporizadorInterval = null;

function agregarMensaje(rol, texto) {
  const div = document.createElement("div");
  div.className = "msg " + (rol === "user" ? "user" : "assistant");
  div.textContent = texto;
  chatDiv.appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

function hablar(texto) {
  estadoDiv.textContent = " Hablando...";
  const utterance = new SpeechSynthesisUtterance(texto);
  utterance.lang = "es-ES";
  utterance.rate = 1.05;
  utterance.onend = () => {
    estadoDiv.textContent = "Presiona el micrófono para hablar";
  };
  speechSynthesis.speak(utterance);
}

// ============================================================
// TEMPORIZADOR — EN EL CHAT COMO MENSAJE
// ============================================================
function formatearTiempo(segundos) {
  const m = Math.floor(segundos / 60);
  const s = segundos % 60;
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function iniciarTemporizador(cantidad, unidad) {
  if (temporizadorActivo) return;
  temporizadorActivo = true;
  const segundosTotales = unidad === "segundos" ? cantidad : cantidad * 60;

  const tempDiv = document.createElement('div');
  tempDiv.className = 'msg assistant temporizador';
  tempDiv.innerHTML = `⏱️ TEMPORIZADOR INICIADO: <span class="temp-valor">${formatearTiempo(segundosTotales)}</span>`;
  chatDiv.appendChild(tempDiv);
  tempDiv.scrollIntoView({ behavior: "smooth" });

  const mensajeInicio = `Temporizador iniciado por ${cantidad} ${unidad}.`;
  hablar(mensajeInicio);

  let restante = segundosTotales;
  const valorSpan = tempDiv.querySelector('.temp-valor');

  temporizadorInterval = setInterval(() => {
    restante--;
    if (restante <= 0) {
      clearInterval(temporizadorInterval);
      temporizadorActivo = false;
      tempDiv.innerHTML = '¡TEMPORIZADOR FINALIZADO!';
      tempDiv.classList.add('temporizador-terminado');
      const mensajeFin = `¡Se cumplió el temporizador de ${cantidad} ${unidad}!`;
      hablar(mensajeFin);
    } else {
      valorSpan.textContent = formatearTiempo(restante);
    }
  }, 1000);
}

// ============================================================
// HORA Y FECHA 
// ============================================================
const PALABRAS_HORA = ["hora"];
const PALABRAS_FECHA = ["día", "dia", "fecha"];
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
               "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const DIAS_SEMANA = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];

function esPreguntaDeHora(texto) {
  const t = texto.toLowerCase();
  if (t.length > 40) return false;
  return PALABRAS_HORA.some(p => t.includes(p)) || PALABRAS_FECHA.some(p => t.includes(p));
}

function horaFormato12(fecha) {
  const h = fecha.getHours();
  const min = String(fecha.getMinutes()).padStart(2, "0");
  if (h === 0) return `12:${min} de la madrugada`;
  if (h < 12) return `${h}:${min} de la mañana`;
  if (h === 12) return `12:${min} del mediodía`;
  if (h < 19) return `${h - 12}:${min} de la tarde`;
  return `${h - 12}:${min} de la noche`;
}

function responderHora(texto) {
  const t = texto.toLowerCase();
  const pidioHora = PALABRAS_HORA.some(p => t.includes(p));
  const pidioFecha = PALABRAS_FECHA.some(p => t.includes(p));
  const ahora = new Date();
  const diaSemana = DIAS_SEMANA[ahora.getDay()];
  const mes = MESES[ahora.getMonth()];
  const horaStr = `son las ${horaFormato12(ahora)}`;

  if (pidioFecha && pidioHora) return `Hoy es ${diaSemana} ${ahora.getDate()} de ${mes}, y ${horaStr}.`;
  if (pidioFecha) return `Hoy es ${diaSemana} ${ahora.getDate()} de ${mes}.`;
  return horaStr.charAt(0).toUpperCase() + horaStr.slice(1) + ".";
}

function esPreguntaDeTemporizador(texto) {
  return texto.toLowerCase().includes("temporizador");
}

function extraerTiempo(texto) {
  const match = texto.match(/\d+/);
  if (!match) return [null, null];
  const cantidad = parseInt(match[0]);
  const unidad = texto.toLowerCase().includes("segundo") ? "segundos" : "minutos";
  return [cantidad, unidad];
}

// ============================================================
// IMAGEN 
// ============================================================
async function enviarImagen(archivo) {
  agregarMensaje("user", `📷 Imagen enviada: ${archivo.name}`);
  estadoDiv.textContent = " Leyendo la imagen...";

  const formData = new FormData();
  formData.append("imagen", archivo);

  try {
    const resp = await fetch("/imagen", { method: "POST", body: formData });
    const datos = await resp.json();
    const respuesta = datos.respuesta || "No pude procesar la imagen.";
    agregarMensaje("assistant", respuesta);
    hablar(respuesta);
  } catch (err) {
    estadoDiv.textContent = " No hay conexión con el servidor.";
    console.error(err);
  } finally {
    cajaImagen.value = "";
  }
}

cajaImagen.addEventListener("change", () => {
  const archivo = cajaImagen.files[0];
  if (archivo) enviarImagen(archivo);
});

// ============================================================
// COMUNICACIÓN CON EL BACKEND
// ============================================================
async function preguntarADamJar(pregunta) {
  agregarMensaje("user", pregunta);
  estadoDiv.textContent = " Pensando...";

  try {
    const resp = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pregunta: pregunta, historial: historial }),
    });
    const datos = await resp.json();
    const respuesta = datos.respuesta || "No pude generar una respuesta.";

    historial.push({ role: "user", content: pregunta });
    historial.push({ role: "assistant", content: respuesta });

    agregarMensaje("assistant", respuesta);
    hablar(respuesta);
  } catch (err) {
    estadoDiv.textContent = " No hay conexión con el servidor.";
    console.error(err);
  }
}

// ============================================================
// MANEJADOR 
// ============================================================
function manejarPregunta(pregunta) {
  if (esPreguntaDeHora(pregunta)) {
    agregarMensaje("user", pregunta);
    const respuesta = responderHora(pregunta);
    agregarMensaje("assistant", respuesta);
    hablar(respuesta);
    return;
  }

  if (esPreguntaDeTemporizador(pregunta)) {
    agregarMensaje("user", pregunta);
    const [cantidad, unidad] = extraerTiempo(pregunta);
    if (cantidad) {
      iniciarTemporizador(cantidad, unidad);
    } else {
      const respuesta = "¿De cuántos minutos o segundos quieres el temporizador?";
      agregarMensaje("assistant", respuesta);
      hablar(respuesta);
    }
    return;
  }

  preguntarADamJar(pregunta);
}

// ============================================================
// RECONOCIMIENTO DE VOZ 
// ============================================================
let reconocimiento = null;
let escuchando = false;

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  reconocimiento = new SpeechRecognition();
  reconocimiento.lang = "es-ES";
  reconocimiento.continuous = false;
  reconocimiento.interimResults = false;

  reconocimiento.onstart = () => {
    escuchando = true;
    micBtn.classList.add("escuchando");
    estadoDiv.textContent = " Escuchando...";
  };

  reconocimiento.onresult = (evento) => {
    const texto = evento.results[0][0].transcript;
    manejarPregunta(texto);
  };

  reconocimiento.onerror = (evento) => {
    estadoDiv.textContent = " No entendí, intenta de nuevo.";
    console.error("Error de reconocimiento:", evento.error);
  };

  reconocimiento.onend = () => {
    escuchando = false;
    micBtn.classList.remove("escuchando");
  };

  micBtn.addEventListener("click", () => {
    if (!escuchando) reconocimiento.start();
  });
} else {
  estadoDiv.textContent = " Tu navegador no soporta reconocimiento de voz. Usa Chrome.";
  micBtn.disabled = true;
}


function enviarTexto() {
  const texto = cajaTexto.value.trim();
  if (!texto) return;
  cajaTexto.value = "";
  manejarPregunta(texto);
}

enviarBtn.addEventListener("click", enviarTexto);
cajaTexto.addEventListener("keydown", (e) => {
  if (e.key === "Enter") enviarTexto();
});


window.addEventListener("load", () => {
  const saludo = "Hola, soy DamJar, tu asistente en la nube. ¿En qué puedo ayudarte?";
  agregarMensaje("assistant", saludo);
  hablar(saludo);
});