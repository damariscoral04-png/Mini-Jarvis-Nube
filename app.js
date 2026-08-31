// ============================================================
// DamJar — Lógica principal del asistente
// ============================================================
if (window.__damjarInicializado) {
  console.warn("app.js ya estaba cargado antes; se ignora esta segunda carga.");
} else {
  window.__damjarInicializado = true;

  // ---------- Referencias al DOM ----------
  const micBtn = document.getElementById("micBtn");
  const estadoDiv = document.getElementById("estado");
  const chatDiv = document.getElementById("chat");
  const cajaTexto = document.getElementById("cajaTexto");
  const enviarBtn = document.getElementById("enviarBtn");
  const cajaImagen = document.getElementById("cajaImagen");
  const historialLista = document.getElementById("historialLista"); // panel derecho
  const cuteRobot = document.querySelector(".cute-robot");

  let historial = [];
  let temporizadorActivo = false;
  let temporizadorInterval = null;

  // ---------- Estado del asistente + expresión del robot ----------
  function setEstado(texto) {
    estadoDiv.textContent = texto;
    if (!cuteRobot) return;
    cuteRobot.classList.remove("hablando", "escuchando", "pensando");
    const t = texto.toLowerCase();
    if (t.includes("hablando")) cuteRobot.classList.add("hablando");
    else if (t.includes("escuchando")) cuteRobot.classList.add("escuchando");
    else if (t.includes("pensando")) cuteRobot.classList.add("pensando");
  }

  function agregarMensaje(rol, texto) {
    const div = document.createElement("div");
    div.className = "msg " + (rol === "user" ? "user" : "assistant");
    div.textContent = texto;
    chatDiv.appendChild(div);
    div.scrollIntoView({ behavior: "smooth" });

    if (rol === "user" && historialLista) {
      const li = document.createElement("li");
      li.textContent = texto.length > 60 ? texto.slice(0, 60) + "…" : texto;
      historialLista.prepend(li); // lo más reciente arriba
    }
  }

  function hablar(texto) {
    setEstado(" Hablando...");
    const utterance = new SpeechSynthesisUtterance(texto);
    utterance.lang = "es-ES";
    utterance.rate = 1.05;
    utterance.onend = () => setEstado("Presiona el micrófono para hablar");
    speechSynthesis.speak(utterance);
  }

  // ============================================================
  // Temporizador -en chat como mensaje
  // ============================================================
  function formatearTiempo(segundos) {
    const m = Math.floor(segundos / 60);
    const s = segundos % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }

  function iniciarTemporizador(cantidad, unidad) {
    if (temporizadorActivo) return;
    temporizadorActivo = true;
    const segundosTotales = unidad === "segundos" ? cantidad : cantidad * 60;

    const tempDiv = document.createElement("div");
    tempDiv.className = "msg assistant temporizador";
    tempDiv.innerHTML = `⏱️ TEMPORIZADOR INICIADO: <span class="temp-valor">${formatearTiempo(segundosTotales)}</span>`;
    chatDiv.appendChild(tempDiv);
    tempDiv.scrollIntoView({ behavior: "smooth" });

    hablar(`Temporizador iniciado por ${cantidad} ${unidad}.`);

    let restante = segundosTotales;
    const valorSpan = tempDiv.querySelector(".temp-valor");

    temporizadorInterval = setInterval(() => {
      restante--;
      if (restante <= 0) {
        clearInterval(temporizadorInterval);
        temporizadorActivo = false;
        tempDiv.innerHTML = "¡TEMPORIZADOR FINALIZADO!";
        tempDiv.classList.add("temporizador-terminado");
        hablar(`¡Se cumplió el temporizador de ${cantidad} ${unidad}!`);
      } else {
        valorSpan.textContent = formatearTiempo(restante);
      }
    }, 1000);
  }

  // ============================================================
  // Hora y Fecha
  // ============================================================
  const PALABRAS_HORA = ["hora"];
  const PALABRAS_FECHA = ["día", "dia", "fecha"];
  const MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
  ];
  const DIAS_SEMANA = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];

  function esPreguntaDeHora(texto) {
    const t = texto.toLowerCase();
    if (t.length > 40) return false;
    return PALABRAS_HORA.some((p) => t.includes(p)) || PALABRAS_FECHA.some((p) => t.includes(p));
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
    const pidioHora = PALABRAS_HORA.some((p) => t.includes(p));
    const pidioFecha = PALABRAS_FECHA.some((p) => t.includes(p));
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
  // Imagen
  // ============================================================
  async function enviarImagen(archivo) {
    agregarMensaje("user", `📷 Imagen enviada: ${archivo.name}`);
    setEstado(" Leyendo la imagen...");

    const formData = new FormData();
    formData.append("imagen", archivo);

    try {
      const resp = await fetch("/imagen", { method: "POST", body: formData });
      const datos = await resp.json();
      const respuesta = datos.respuesta || "No pude procesar la imagen.";
      agregarMensaje("assistant", respuesta);
      hablar(respuesta);
    } catch (err) {
      setEstado(" No hay conexión con el servidor.");
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
  // Comunicacion con el backend
  // ============================================================
  async function preguntarADamJar(pregunta) {
    agregarMensaje("user", pregunta);
    setEstado(" Pensando...");

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
      setEstado(" No hay conexión con el servidor.");
      console.error(err);
    }
  }

  // ============================================================
  // Manejador central (texto o voz llegan aquí por igual)
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
  // Reconocimiento de voz
  // ============================================================
  let reconocimiento = null;
  let escuchando = false;
  let yaSeProceso = false; 

  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    reconocimiento = new SpeechRecognition();
    reconocimiento.lang = "es-ES";
    reconocimiento.continuous = false; 
    reconocimiento.interimResults = false;
    reconocimiento.maxAlternatives = 1;

    reconocimiento.onstart = () => {
      escuchando = true;
      yaSeProceso = false;
      micBtn.classList.add("escuchando");
      setEstado(" Escuchando...");
    };

    reconocimiento.onresult = (evento) => {


      if (yaSeProceso) return;
      yaSeProceso = true;
      const texto = evento.results[0][0].transcript;
      manejarPregunta(texto);
    };

    reconocimiento.onerror = (evento) => {
      setEstado(" No entendí, intenta de nuevo.");
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
    setEstado(" Tu navegador no soporta reconocimiento de voz. Usa Chrome.");
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

  // ============================================================
  // Panel del historial — mostrar / ocultar con la flecha
  // ============================================================
  const sidebar = document.getElementById("chatHistory");
  const toggleBtn = document.getElementById("toggleHistory");

  if (sidebar && toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("collapsed");
      toggleBtn.textContent = sidebar.classList.contains("collapsed") ? "▶" : "◀";
    });
  }

  // ============================================================
  // Mensaje de Bienvenida
  // ============================================================
  window.addEventListener("load", () => {
    const saludo = "Hola, soy Damjar, tu asistente en la nube. ¿En qué puedo ayudarte?";
    agregarMensaje("assistant", saludo);
    hablar(saludo);
  });

  // ============================================================
  // Orbe de audio animado (canvas detrás del micrófono)
  // ============================================================
  (function () {
    const canvas = document.getElementById("orbCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const centro = { x: canvas.width / 2, y: canvas.height / 2 };

    const NUM_PARTICULAS = 90;
    const particulas = [];
    for (let i = 0; i < NUM_PARTICULAS; i++) {
      particulas.push({
        angulo: Math.random() * Math.PI * 2,
        radio: 12 + Math.random() * 38,
        velocidad: 0.003 + Math.random() * 0.007,
        tamano: 1 + Math.random() * 2,
        offset: Math.random() * Math.PI * 2,
      });
    }

    let intensidad = 1;
    function actualizarIntensidad() {
      const texto = estadoDiv ? estadoDiv.textContent : "";
      intensidad =
        texto.includes("Pensando") || texto.includes("Hablando") || texto.includes("Escuchando") ? 2.1 : 1;
    }

    function dibujar() {
      ctx.fillStyle = "rgba(46, 26, 71, 0.28)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      actualizarIntensidad();

      const nucleo = ctx.createRadialGradient(centro.x, centro.y, 0, centro.x, centro.y, 20 * intensidad);
      nucleo.addColorStop(0, "rgba(216, 180, 254, 0.95)");
      nucleo.addColorStop(1, "rgba(216, 180, 254, 0)");
      ctx.fillStyle = nucleo;
      ctx.beginPath();
      ctx.arc(centro.x, centro.y, 20 * intensidad, 0, Math.PI * 2);
      ctx.fill();

      for (const p of particulas) {
        p.angulo += p.velocidad * intensidad;
        const radioAnimado = p.radio + Math.sin(p.angulo * 3 + p.offset) * 5;
        const x = centro.x + Math.cos(p.angulo) * radioAnimado;
        const y = centro.y + Math.sin(p.angulo) * radioAnimado * 0.6;

        ctx.beginPath();
        ctx.arc(x, y, p.tamano, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(192, 132, 252, 0.9)";
        ctx.shadowColor = "rgba(168, 85, 247, 0.9)";
        ctx.shadowBlur = 7 * intensidad;
        ctx.fill();
      }
      ctx.shadowBlur = 0;

      requestAnimationFrame(dibujar);
    }

    dibujar();
  })();
} 