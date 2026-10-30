/**
 * app.js: maneja los eventos de la interfaz y el renderizado del DOM.
 * No conoce fetch ni URLs -- eso vive en api.js. Aquí solo se traduce
 * la respuesta ya obtenida en HTML visible para el usuario.
 */

cdocument.addEventListener('DOMContentLoaded', () => {
    // Referencias a los contenedores HTML (asegúrate de que estos IDs existan en tu index.html)
    const formLogin = document.getElementById('form-login');
    const seccionLogin = document.getElementById('seccion-login');
    const seccionDashboard = document.getElementById('seccion-dashboard');
    const contenedorHistorial = document.getElementById('contenedor-historial');
    const btnCerrarSesion = document.getElementById('btn-cerrar-sesion');

    // 1. Control de Sesión al cargar la página
    if (API.getToken()) {
        mostrarDashboard();
    } else {
        mostrarLogin();
    }

    // 2. Evento de Login
    if (formLogin) {
        formLogin.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            try {
                await API.login(email, password);
                mostrarDashboard();
            } catch (error) {
                alert(error.message);
            }
        });
    }

    // 3. Evento de Cerrar Sesión
    if (btnCerrarSesion) {
        btnCerrarSesion.addEventListener('click', () => {
            API.logout();
            mostrarLogin();
        });
    }

    // 4. Funciones de actualización asíncrona de UI
    async function mostrarDashboard() {
        seccionLogin.style.display = 'none';
        seccionDashboard.style.display = 'block';
        
        try {
            // Para esta prueba usamos la planta ID 1 (la que inyectamos con seed.py)
            const historial = await API.getHistorial(1);
            renderizarHistorial(historial);
        } catch (error) {
            contenedorHistorial.innerHTML = `<p style="color:red;">Error: ${error.message}</p>`;
            if (error.message.includes('NO_AUTORIZADO') || error.message.includes('TOKEN_EXPIRADO')) {
                API.logout();
                mostrarLogin();
            }
        }
    }

    function mostrarLogin() {
        seccionLogin.style.display = 'block';
        seccionDashboard.style.display = 'none';
    }

    function renderizarHistorial(datos) {
        if (!contenedorHistorial) return;
        contenedorHistorial.innerHTML = '';
        
        if (datos.length === 0) {
            contenedorHistorial.innerHTML = '<p>No hay mediciones aún.</p>';
            return;
        }

        datos.forEach(medicion => {
            const div = document.createElement('div');
            div.className = 'tarjeta-medicion'; // Usa la clase CSS de tu maquetación
            div.innerHTML = `
                <p><strong>Fecha:</strong> ${new Date(medicion.fecha).toLocaleString()}</p>
                <p><strong>Temp:</strong> ${medicion.valores.temperatura}°C | <strong>Hum:</strong> ${medicion.valores.humedad}% | <strong>Luz:</strong> ${medicion.valores.luz}lx</p>
                <hr>
            `;
            contenedorHistorial.appendChild(div);
        });
    }
});