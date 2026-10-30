function mostrarPantalla(idActiva) {
    document.querySelectorAll('.pantalla').forEach(p => p.classList.remove('activa'));
    document.getElementById(`pantalla-${idActiva}`).classList.add('activa');
    document.getElementById('menu-inferior').style.display = (idActiva === 'login') ? 'none' : 'flex';
    
    localStorage.setItem('pantalla_actual', idActiva);
    
    if (idActiva === 'detalles') cargarDetalles();
    if (idActiva === 'historial') cargarHistorial();
}

function getBadge(estado) {
    if (estado === "OPTIMO") return '<span class="badge optimo">Óptimo</span>';
    if (estado === "ALTO") return '<span class="badge alerta">Alto</span>';
    return '<span class="badge bajo">Bajo</span>';
}

async function cargarDetalles() {
    try {
        const historial = await API.getHistorial(1);
        const estadoActualDiv = document.getElementById('estado-actual');
        const recomendacionesDiv = document.getElementById('recomendaciones-actuales');
        const fechaLabel = document.getElementById('fecha-medicion');
        
        if (historial.length > 0) {
            const ultima = historial[0];
            
            const fechaObj = new Date(ultima.fecha);
            fechaLabel.innerText = fechaObj.toLocaleDateString() + ' - ' + fechaObj.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

            estadoActualDiv.innerHTML = `
                <div class="tarjeta-medicion">
                    ${getBadge(ultima.detalle_parametros.temperatura)}
                    <p>🌡️ Temperatura</p>
                    <h3>${ultima.valores.temperatura}°C</h3>
                </div>
                <div class="tarjeta-medicion">
                    ${getBadge(ultima.detalle_parametros.humedad)}
                    <p>💧 Humedad</p>
                    <h3>${ultima.valores.humedad}%</h3>
                </div>
                <div class="tarjeta-medicion" style="width: 100%;">
                    ${getBadge(ultima.detalle_parametros.luz)}
                    <p>☀️ Luz</p>
                    <h3>${ultima.valores.luz} lux</h3>
                </div>
            `;

            recomendacionesDiv.innerHTML = ultima.recomendaciones.map(r => `<p>• ${r}</p>`).join('');

        } else {
            estadoActualDiv.innerHTML = `<p style="padding:15px;">Aún no hay datos de sensores.</p>`;
            recomendacionesDiv.innerHTML = `<p>Esperando la primera medición...</p>`;
            fechaLabel.innerText = "--";
        }
    } catch (error) {
        console.error("Error cargando detalles", error);
    }
}

async function cargarHistorial() {
    const contenedor = document.getElementById('contenedor-historial');
    contenedor.innerHTML = 'Cargando historial...';
    try {
        const historial = await API.getHistorial(1);
        contenedor.innerHTML = '';
        historial.forEach(m => {
            const colorBorder = m.estado_general === 'SALUDABLE' ? '#2ecc71' : '#e74c3c';
            contenedor.innerHTML += `
                <div class="tarjeta" style="border-left: 5px solid ${colorBorder}">
                    <p><strong>${new Date(m.fecha).toLocaleString()}</strong></p>
                    <p>Temp: ${m.valores.temperatura}°C | Hum: ${m.valores.humedad}% | Luz: ${m.valores.luz}lx</p>
                    <p style="font-size:12px; color:#666; margin-top:5px;">Estado: ${m.estado_general.replace('_', ' ')}</p>
                </div>
            `;
        });
    } catch (error) {
        contenedor.innerHTML = `<p style="color:red;">Error al cargar: ${error.message}</p>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (API.getToken()) {
        const pantallaGuardada = localStorage.getItem('pantalla_actual') || 'mis-plantas';
        mostrarPantalla(pantallaGuardada);
    } else {
        mostrarPantalla('login');
    }

    document.getElementById('form-login').addEventListener('submit', async (e) => {
        e.preventDefault();
        try {
            await API.login(document.getElementById('email').value, document.getElementById('password').value);
            mostrarPantalla('mis-plantas');
        } catch (error) { alert('Error: ' + error.message); }
    });

    document.getElementById('btn-cerrar-sesion').addEventListener('click', () => {
        API.logout();
        localStorage.removeItem('pantalla_actual');
        mostrarPantalla('login');
    });

    document.getElementById('btn-ir-detalles').addEventListener('click', () => mostrarPantalla('detalles'));

    const menuDesplegable = document.getElementById('menu-desplegable');
    document.getElementById('btn-opciones').addEventListener('click', (e) => {
        menuDesplegable.style.display = menuDesplegable.style.display === 'block' ? 'none' : 'block';
        e.stopPropagation();
    });

    document.getElementById('btn-ver-historial').addEventListener('click', () => {
        menuDesplegable.style.display = 'none';
        mostrarPantalla('historial');
    });

    document.addEventListener('click', () => {
        if(menuDesplegable) menuDesplegable.style.display = 'none';
    });
});