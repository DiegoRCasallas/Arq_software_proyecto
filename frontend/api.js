/**
 * ApiCliente: única parte del frontend que sabe cómo hablar con el
 * backend (fetch, headers, URLs). El resto de la aplicación (app.js)
 * no debería saber que existe HTTP -- solo pide "diagnosticar" o
 * "listar especies" y recibe datos o un error ya interpretado.
 *
 * RA2: todas las peticiones son asíncronas (fetch + async/await),
 * la página nunca se recarga al consultar un diagnóstico.
 */
const ApiCliente = {
  async listarEspecies() {
    const respuesta = await fetch(`${CONFIG.API_BASE_URL}/especies`);
    if (!respuesta.ok) {
      throw new Error("No fue posible cargar la lista de especies.");
    }
    return respuesta.json();
  },

  async diagnosticar({ especie, humedad, temperatura, luz }) {
    const respuesta = await fetch(`${CONFIG.API_BASE_URL}/diagnostico`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ especie, humedad, temperatura, luz }),
    });

    const cuerpo = await respuesta.json();

    if (!respuesta.ok) {
      // El backend siempre responde con {error, mensaje} en caso de fallo (RF6)
      const error = new Error(cuerpo.mensaje || "Ocurrió un error al diagnosticar la planta.");
      error.codigo = cuerpo.error;
      error.status = respuesta.status;
      throw error;
    }

    return cuerpo;
  },
};
