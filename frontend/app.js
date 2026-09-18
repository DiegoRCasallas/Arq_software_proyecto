/**
 * app.js: maneja los eventos de la interfaz y el renderizado del DOM.
 * No conoce fetch ni URLs -- eso vive en api.js. Aquí solo se traduce
 * la respuesta ya obtenida en HTML visible para el usuario.
 */

const ESTILOS_POR_ESTADO = {
  BAJO: "estado-bajo",
  OPTIMO: "estado-optimo",
  ALTO: "estado-alto",
};

const ESTILOS_POR_INDICE = {
  SALUDABLE: "indice-saludable",
  EN_RIESGO: "indice-en-riesgo",
  CRITICO: "indice-critico",
};

const ETIQUETAS_INDICE = {
  SALUDABLE: "🌿 Saludable",
  EN_RIESGO: "⚠️ En riesgo",
  CRITICO: "🚨 Crítico",
};

function poblarSelectorEspecies(especies) {
  const select = document.getElementById("especie");
  select.innerHTML = "";

  if (especies.length === 0) {
    select.innerHTML = '<option value="" disabled selected>No hay especies disponibles</option>';
    return;
  }

  const opcionPorDefecto = document.createElement("option");
  opcionPorDefecto.value = "";
  opcionPorDefecto.disabled = true;
  opcionPorDefecto.selected = true;
  opcionPorDefecto.textContent = "Selecciona una especie";
  select.appendChild(opcionPorDefecto);

  for (const perfil of especies) {
    const opcion = document.createElement("option");
    opcion.value = perfil.especie;
    opcion.textContent = capitalizar(perfil.especie);
    select.appendChild(opcion);
  }
}

function renderizarListaEspecies(especies) {
  const contenedor = document.getElementById("lista-especies");

  if (especies.length === 0) {
    contenedor.innerHTML = "<p>No hay especies disponibles.</p>";
    return;
  }

  contenedor.innerHTML = especies
    .map(
      (perfil) => `
      <article class="tarjeta-especie">
        <h3>${capitalizar(perfil.especie)}</h3>
        <ul>
          <li><strong>Humedad:</strong> ${perfil.rangos.humedad.optimo_min}% – ${perfil.rangos.humedad.optimo_max}%</li>
          <li><strong>Luz:</strong> ${perfil.rangos.luz.optimo_min} – ${perfil.rangos.luz.optimo_max} lux</li>
          <li><strong>Temperatura:</strong> ${perfil.rangos.temperatura.optimo_min}°C – ${perfil.rangos.temperatura.optimo_max}°C</li>
        </ul>
      </article>
    `
    )
    .join("");
}

function mostrarResultado(diagnostico) {
  ocultar("seccion-error");
  mostrar("seccion-resultado");

  const badge = document.getElementById("indice-vitalidad");
  badge.textContent = ETIQUETAS_INDICE[diagnostico.indice_vitalidad] || diagnostico.indice_vitalidad;
  badge.className = `badge ${ESTILOS_POR_INDICE[diagnostico.indice_vitalidad] || ""}`;

  actualizarEstado("estado-humedad", diagnostico.estados.humedad);
  actualizarEstado("estado-luz", diagnostico.estados.luz);
  actualizarEstado("estado-temperatura", diagnostico.estados.temperatura);

  const listaRecomendaciones = document.getElementById("lista-recomendaciones");
  const contenedorRecomendaciones = document.getElementById("recomendaciones-contenedor");

  if (diagnostico.recomendaciones.length === 0) {
    contenedorRecomendaciones.hidden = true;
  } else {
    contenedorRecomendaciones.hidden = false;
    listaRecomendaciones.innerHTML = diagnostico.recomendaciones
      .map((texto) => `<li>${texto}</li>`)
      .join("");
  }
}

function actualizarEstado(idElemento, estado) {
  const elemento = document.getElementById(idElemento);
  elemento.textContent = estado;
  elemento.className = `valor-estado ${ESTILOS_POR_ESTADO[estado] || ""}`;
}

function mostrarError(mensaje) {
  ocultar("seccion-resultado");
  mostrar("seccion-error");
  document.getElementById("mensaje-error").textContent = mensaje;
}

function mostrar(idSeccion) {
  document.getElementById(idSeccion).hidden = false;
}

function ocultar(idSeccion) {
  document.getElementById(idSeccion).hidden = true;
}

function capitalizar(texto) {
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

async function cargarEspecies() {
  try {
    const especies = await ApiCliente.listarEspecies();
    poblarSelectorEspecies(especies);
    renderizarListaEspecies(especies);
  } catch (error) {
    document.getElementById("lista-especies").innerHTML =
      '<p class="mensaje-error">No fue posible cargar las especies. ¿Está el backend corriendo?</p>';
  }
}

function inicializarFormulario() {
  const formulario = document.getElementById("form-diagnostico");
  const botonSubmit = document.getElementById("btn-diagnosticar");

  formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault(); // RA2: nunca recargar la página

    const datos = {
      especie: document.getElementById("especie").value,
      humedad: document.getElementById("humedad").value,
      temperatura: document.getElementById("temperatura").value,
      luz: document.getElementById("luz").value,
    };

    botonSubmit.disabled = true;
    botonSubmit.textContent = "Diagnosticando...";

    try {
      const diagnostico = await ApiCliente.diagnosticar(datos);
      mostrarResultado(diagnostico);
    } catch (error) {
      mostrarError(error.message);
    } finally {
      botonSubmit.disabled = false;
      botonSubmit.textContent = "Diagnosticar";
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  cargarEspecies();
  inicializarFormulario();
});
