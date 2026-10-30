// Enrutador simple para cambiar entre pantallas
function mostrarPantalla(idActiva) {
    document.querySelectorAll('.pantalla').forEach(p => p.classList.remove('activa'));
    document.getElementById(`pantalla-${idActiva}`).classList.add('activa');
    
    // El menú inferior no se muestra en el login
    document.getElementById('menu-inferior').style.display = (idActiva === 'login') ? 'none' : 'flex';
}

document.addEventListener('DOMContentLoaded', () => {
    // Verificar sesión al inicio
    if (API.getToken()) {
        mostrarPantalla('mis-plantas');
    }

    // 1. Manejo del Login
    document.getElementById('form-login').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        try {
            await API.login(email, password);
            mostrarPantalla('mis-plantas');
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });

    // 2. Cerrar Sesión
    document.getElementById('btn-cerrar-sesion').addEventListener('click', () => {
        API.logout();
        mostrarPantalla('login');
    });

    // 3. Navegación a Detalles de Planta
    document.getElementById('btn-ver-detalles').addEventListener('click', async () => {
        mostrarPantalla('detalles');
        
        try {
            // Consulta el historial de la planta ID 1 y toma el último registro
            const historial = await API.getHistorial(1);
            const estadoActualDiv = document.getElementById('estado-actual');
            
            if (historial.length > 0) {
                const ultima = historial[0]; // El backend ya los devuelve ordenados descendentes
                estadoActualDiv.innerHTML = `
                    <p><strong>Última actualización:</strong> ${new Date(ultima.fecha).toLocaleString()}</p>
                    <p><strong>Temperatura:</strong> ${ultima.valores.temperatura} °C</p>
                    <p><strong>Humedad:</strong> ${ultima.valores.humedad} %</p>
                    <p><strong>Luz:</strong> ${ultima.valores.luz} lux</p>
                `;
            } else {
                estadoActualDiv.innerHTML = `<p>Aún no hay datos de sensores.</p>`;
            }
        } catch (error) {
            console.error("Error al cargar detalles", error);
        }
    });

    // 4. Menú de 3 puntos y navegación a Historial
    const menuDesplegable = document.getElementById('menu-desplegable');
    document.getElementById('btn-menu-puntos').addEventListener('click', () => {
        menuDesplegable.style.display = menuDesplegable.style.display === 'none' ? 'block' : 'none';
    });

    document.getElementById('btn-ver-historial').addEventListener('click', async () => {
        menuDesplegable.style.display = 'none';
        mostrarPantalla('historial');
        
        const contenedor = document.getElementById('contenedor-historial');
        contenedor.innerHTML = 'Cargando historial...';
        
        try {
            const historial = await API.getHistorial(1);
            contenedor.innerHTML = '';
            historial.forEach(m => {
                contenedor.innerHTML += `
                    <div class="tarjeta">
                        <p><strong>${new Date(m.fecha).toLocaleString()}</strong></p>
                        <p>Temp: ${m.valores.temperatura}°C | Hum: ${m.valores.humedad}% | Luz: ${m.valores.luz}lux</p>
                    </div>
                `;
            });
        } catch (error) {
            contenedor.innerHTML = `<p style="color:red;">Error al cargar: ${error.message}</p>`;
        }
    });
});