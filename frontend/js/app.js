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
            const historial = await API.getHistorial(1);
            const estadoActualDiv = document.getElementById('estado-actual');
            const recomendacionesDiv = document.getElementById('recomendaciones-actuales');
            
            if (historial.length > 0) {
                const ultima = historial[0];
                
                // 1. Renderizar tarjetas de medición
                estadoActualDiv.innerHTML = `
                    <div class="tarjeta-medicion">
                        <p>🌡️ Temperatura</p>
                        <h3>${ultima.valores.temperatura}°C</h3>
                    </div>
                    <div class="tarjeta-medicion">
                        <p>💧 Humedad</p>
                        <h3>${ultima.valores.humedad}%</h3>
                    </div>
                    <div class="tarjeta-medicion" style="width: 100%;">
                        <p>☀️ Luz</p>
                        <h3>${ultima.valores.luz} lux</h3>
                    </div>
                `;

                // 2. Generar recomendaciones dinámicas basadas en los valores
                let recsHTML = "";
                if (ultima.valores.humedad < 40) {
                    recsHTML += "<p>🌊 <strong>Aumentar riego:</strong> El sustrato está muy seco.</p>";
                } else {
                    recsHTML += "<p>🌊 <strong>Regar cada 3-4 días:</strong> Mantén la humedad actual.</p>";
                }
                
                if (ultima.valores.luz < 500) {
                    recsHTML += "<p>💡 <strong>Mover planta:</strong> Necesita más iluminación.</p>";
                } else {
                    recsHTML += "<p>💡 <strong>Luz adecuada:</strong> Proporciona luz brillante e indirecta.</p>";
                }

                recsHTML += "<p>🧪 <strong>Fertiliza:</strong> Mensualmente durante la temporada de crecimiento.</p>";
                
                recomendacionesDiv.innerHTML = recsHTML;

            } else {
                estadoActualDiv.innerHTML = `<p style="padding:15px;">Aún no hay datos de sensores.</p>`;
                recomendacionesDiv.innerHTML = `<p>Esperando la primera medición...</p>`;
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