 const appState = {
    plantId: null,
    plant: null,
    plants: [],
    toastTimer: null,
};

let medicionesSocket = null;
let socketReintento = null;
let socketHeartbeat = null;
let qrStream = null;
let qrScanTimer = null;
let qrPairingAttempt = 0;
let qrPairingSessionId = null;

const PARAMETER_LABELS = {
    temperatura: 'Temperatura',
    humedad: 'Humedad ambiental',
    luz: 'Luz',
};

const CARITAS_ANIMO = {
    FELIZ:       { cara: '( ˘ ▽ ˘ )',     texto: '¡Estoy feliz!',         color: '#1f7a4c' },
    SEDIENTA:    { cara: '( ಥ_ಥ )',       texto: '¡Ambiente muy seco!',   color: '#2563eb' },
    AHOGADA:     { cara: '( ◎_◎; ) ~',    texto: '¡Aire muy húmedo!',     color: '#1d4ed8' },
    SOFOCADA:    { cara: '( ＠_＠; )',     texto: '¡Hace mucho calor!',    color: '#dc2626' },
    CON_FRIO:    { cara: '( ≧﹏≦ )',      texto: '¡Tengo frío!',          color: '#0284c7' },
    SIN_LUZ:     { cara: '( -_- )',       texto: 'Necesito más luz',      color: '#d97706' },
    DESLUMBRADA: { cara: '( >_< ) ☀',     texto: '¡Demasiada luz!',       color: '#ea580c' },
    DORMIDA:     { cara: '( ˘ω˘ ) zZ',    texto: 'Descansando…',          color: '#6d28d9' },
    EN_RIESGO:   { cara: '( x _ x )',     texto: '¡Revisa mis sensores!', color: '#dc2626' },
};

const ETAPAS_EVOLUCION = [
    { nivelMin: 1, icono: '🌰', titulo: 'Semilla',      desc: 'Recién plantada' },
    { nivelMin: 2, icono: '🌱', titulo: 'Brote',        desc: 'Primeras hojitas' },
    { nivelMin: 3, icono: '🌿', titulo: 'Planta joven', desc: 'Creciendo fuerte' },
    { nivelMin: 4, icono: '🪴', titulo: 'Planta adulta', desc: 'Muy bien cuidada' },
    { nivelMin: 5, icono: '🌸', titulo: 'En floración', desc: '¡Maestra botánica!' },
];

function obtenerEtapaEvolucion(nivel) {
    let etapa = ETAPAS_EVOLUCION[0];
    for (const item of ETAPAS_EVOLUCION) {
        if (nivel >= item.nivelMin) etapa = item;
    }
    return etapa;
}

const CARE_TIPS = {
    cinta: [
        'Prefiere humedad ambiental moderada; pulveriza sus hojas si el aire está muy seco.',
        'Prefiere luz indirecta y espacios bien iluminados.',
        'Riega cuando la capa superior del sustrato empiece a secarse, sin encharcar.',
    ],
    albahaca: [
        'Requiere al menos 6 horas de luz solar o iluminación muy brillante.',
        'Agradece una buena ventilación para evitar exceso de humedad en sus hojas.',
        'Poda los brotes florales para estimular hojas frescas y densas.',
    ],
    poto: [
        'Tolera bien luz indirecta moderada y sombra parcial.',
        'Se adapta bien a humedad ambiental media (45% - 70%).',
        'Limpia sus hojas ocasionalmente para mejorar la absorción de luz.',
    ],
    suculenta: [
        'Prefiere ambientes secos y bien ventilados; evita lugares con mucha humedad en el aire.',
        'Ubícala en un lugar con abundante luz directa para mantener su color.',
        'Riega de forma espaciada y usa macetas con buen drenaje.',
    ],
    helecho: [
        'Necesita alta humedad ambiental; pulveriza agua cerca de sus frondas con frecuencia.',
        'Prefiere luz suave filtrada o semisombra; evita el sol directo.',
        'Mantén el sustrato ligeramente húmedo, sin permitir que se seque del todo.',
    ],
    orquidea: [
        'Disfruta de humedad ambiental elevada (55% - 80%) con buena circulación de aire.',
        'Necesita luz indirecta abundante pero nunca sol directo que queme sus hojas.',
        'Utiliza sustrato poroso de corteza de pino para que sus raíces respiren.',
    ],
};

function escapeHTML(value) {
    return String(value ?? '').replace(/[&<>"']/g, (character) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
    })[character]);
}

function traducirEstado(estado) {
    return ({
        SALUDABLE: 'Saludable',
        EN_RIESGO: 'En riesgo',
        CRITICO: 'Crítico',
        INDETERMINADO: 'Sin diagnóstico',
        BAJO: 'Bajo',
        OPTIMO: 'Óptimo',
        ALTO: 'Alto',
        REPOSO_NOCTURNO: 'En reposo (noche)',
    })[estado] || 'Sin datos';
}

function claseEstado(estado) {
    return ({
        SALUDABLE: 'healthy',
        EN_RIESGO: 'warning',
        CRITICO: 'critical',
        INDETERMINADO: 'neutral',
        BAJO: 'warning',
        OPTIMO: 'healthy',
        ALTO: 'warning',
        REPOSO_NOCTURNO: 'healthy',
    })[estado] || 'neutral';
}

function valorConUnidad(parametro, valor) {
    const unidades = { temperatura: '°C', humedad: '%', luz: 'lux' };
    const numero = Number(valor);
    const formato = Number.isFinite(numero)
        ? new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 }).format(numero)
        : '—';
    return `${formato} ${unidades[parametro] || ''}`.trim();
}

function mostrarToast(mensaje, tipo = 'info') {
    const toast = document.getElementById('toast');
    window.clearTimeout(appState.toastTimer);
    toast.textContent = mensaje;
    toast.className = `toast ${tipo}`;
    toast.hidden = false;
    appState.toastTimer = window.setTimeout(() => { toast.hidden = true; }, 4200);
}

function mostrarPantalla(idActiva) {
    const requiereSesion = !['bienvenida', 'login', 'registro'].includes(idActiva);
    if (requiereSesion && !API.getToken()) idActiva = 'bienvenida';

    if (idActiva !== 'conectar') {
        cancelarVinculacionQR(false);
    }

    document.querySelectorAll('.pantalla').forEach((pantalla) => {
        pantalla.classList.toggle('activa', pantalla.id === `pantalla-${idActiva}`);
    });

    const nav = document.getElementById('menu-inferior');
    const esPantallaAcceso = ['bienvenida', 'login', 'registro'].includes(idActiva);
    const navVisible = Boolean(API.getToken()) && !esPantallaAcceso && !['diagnostico', 'minijuego', 'conectar', 'ajustes'].includes(idActiva);
    nav.hidden = !navVisible;
    document.body.classList.toggle('diagnosis-active', idActiva === 'diagnostico');
    document.querySelectorAll('.nav-item').forEach((item) => {
        item.classList.toggle('active', item.dataset.screen === idActiva);
    });

    localStorage.setItem('pantalla_actual', idActiva);
    if (idActiva !== 'minijuego') detenerMinijuego();
    if (idActiva === 'mis-plantas') cargarPlantas();
    if (idActiva === 'detalles') cargarDetalles();
    if (idActiva === 'historial') cargarHistorial();
    if (idActiva === 'diagnostico') cargarDiagnostico();
    if (idActiva === 'minijuego') prepararMinijuego();
    if (idActiva === 'add-planta') cargarEspecies();
    if (idActiva === 'ajustes') cargarAjustes();
    if (idActiva === 'conectar') cargarConectarDispositivo();
}

function renderVacio(contenedor, titulo, mensaje, accion = '') {
    contenedor.innerHTML = `
        <div class="empty-state">
            <span class="empty-icon" aria-hidden="true">🌱</span>
            <h2>${escapeHTML(titulo)}</h2>
            <p>${escapeHTML(mensaje)}</p>
            ${accion}
        </div>`;
}

async function cargarPlantas() {
    const contenedor = document.getElementById('lista-plantas');
    contenedor.innerHTML = '<p class="loading-message">Cargando tus plantas…</p>';
    try {
        appState.plants = await API.getPlants();
        if (!appState.plants.length) {
            renderVacio(
                contenedor,
                'Tu jardín empieza aquí',
                'Añade tu primera planta para empezar a conocer cómo se siente.',
                '<button class="btn btn-primary" type="button" data-screen="add-planta">Añadir planta</button>',
            );
            return;
        }

        contenedor.innerHTML = appState.plants.map((planta) => {
            const ultima = planta.ultima_medicion;
            const estado = ultima?.estado_general || 'INDETERMINADO';
            const nombre = planta.apodo || planta.especie;
            const detalleLectura = ultima
                ? `Agua ${valorConUnidad('humedad', ultima.valores.humedad)} · Luz ${valorConUnidad('luz', ultima.valores.luz)}`
                : 'Sin datos de sensores aún';
            return `
                <button class="plant-card" type="button" data-plant-id="${escapeHTML(planta.id)}">
                    <span class="plant-avatar" aria-hidden="true">🪴</span>
                    <span class="plant-card-content">
                        <span class="plant-card-top"><strong>${escapeHTML(nombre)}</strong><span class="status-pill ${claseEstado(estado)}">${traducirEstado(estado)}</span></span>
                        <span class="plant-species">${escapeHTML(planta.especie)} · Nivel ${escapeHTML(planta.gamificacion?.nivel ?? 1)}</span>
                        <span class="plant-reading">${escapeHTML(detalleLectura)}</span>
                    </span>
                    <span class="plant-chevron" aria-hidden="true">›</span>
                </button>`;
        }).join('');
    } catch (error) {
        contenedor.innerHTML = '';
        renderVacio(contenedor, 'No pudimos cargar tus plantas', error.message,
            '<button class="btn btn-outline" type="button" data-retry="plants">Intentar de nuevo</button>');
    }
}

function renderMediciones(contenedor, medicion) {
    if (!medicion) {
        contenedor.innerHTML = '<div class="inline-empty"><span aria-hidden="true">⌁</span><p>Aún no hay lecturas. Cuando el dispositivo envíe su primera medición, aparecerá aquí.</p></div>';
        return;
    }
    const parametros = Object.keys(medicion.valores || {});
    contenedor.innerHTML = parametros.map((parametro) => {
        const estado = medicion.detalle_parametros?.[parametro] || 'INDETERMINADO';
        return `
            <article class="metric-card">
                <span class="metric-icon" aria-hidden="true">${parametro === 'temperatura' ? '🌡️' : parametro === 'humedad' ? '💧' : '☀️'}</span>
                <span class="metric-label">${escapeHTML(PARAMETER_LABELS[parametro] || parametro)}</span>
                <strong>${escapeHTML(valorConUnidad(parametro, medicion.valores[parametro]))}</strong>
                <span class="metric-state ${claseEstado(estado)}">${traducirEstado(estado)}</span>
            </article>`;
    }).join('');
}

function renderRecomendaciones(contenedor, medicion) {
    if (!medicion) {
        contenedor.innerHTML = '<p class="muted">Las recomendaciones aparecerán después de recibir una medición.</p>';
    } else if (medicion.recomendaciones?.length) {
        contenedor.innerHTML = `<ul class="recommendation-list">${medicion.recomendaciones.map((texto) => `<li>${escapeHTML(texto)}</li>`).join('')}</ul>`;
    } else {
        contenedor.innerHTML = '<p class="success-note">¡Todo está en su rango ideal! Sigue con sus cuidados habituales.</p>';
    }
}

function renderUltimaMedicion(medicion) {
    renderMediciones(document.getElementById('estado-actual'), medicion);
    renderRecomendaciones(document.getElementById('recomendaciones-actuales'), medicion);
    document.getElementById('fecha-medicion').textContent = medicion
        ? new Date(medicion.fecha).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
        : 'Sin datos';
}

async function cargarDetalles() {
    const perfil = document.getElementById('detalle-planta');
    if (!appState.plantId) {
        mostrarPantalla('mis-plantas');
        return;
    }
    perfil.className = 'detail-profile loading-message';
    perfil.textContent = 'Cargando información…';
    try {
        const planta = await API.getPlant(appState.plantId);
        appState.plant = planta;

        const gamif = planta.gamificacion || {
            nivel: 1,
            xp_nivel_actual: 0,
            xp_siguiente_nivel: 100,
            porcentaje_nivel: 0,
            estado_animo: 'FELIZ',
        };
        const animo = CARITAS_ANIMO[gamif.estado_animo] || CARITAS_ANIMO.FELIZ;
        const etapa = obtenerEtapaEvolucion(gamif.nivel); // <-- 1. Calcular etapa

        perfil.className = 'detail-profile';
        perfil.innerHTML = `
            <div class="large-plant-avatar gamif-avatar" aria-label="${escapeHTML(animo.texto)}">
                <span class="gamif-face" style="color: ${animo.color};">${escapeHTML(animo.cara)}</span>
                <span class="gamif-mood">${escapeHTML(animo.texto)}</span>
            </div>
            <div class="detail-profile-copy">
                <span class="eyebrow">${escapeHTML(planta.especie)}</span>
                <h2>${escapeHTML(planta.apodo || planta.especie)}</h2>
                <span class="connection-note ${planta.dispositivo_conectado ? 'connected' : ''}">${planta.dispositivo_conectado ? '● Dispositivo conectado' : '○ Dispositivo pendiente de conexión'}</span>
                <div class="gamif-progress">
                    <div class="gamif-progress-header">
                        <strong><span class="etapa-badge">${etapa.icono} ${escapeHTML(etapa.titulo)}</span> · Nivel ${escapeHTML(gamif.nivel)}</strong>
                        <span>${escapeHTML(gamif.xp_nivel_actual)} / ${escapeHTML(gamif.xp_siguiente_nivel)} XP</span>
                    </div>
                    <div class="gamif-xp-bar" role="progressbar" aria-valuenow="${escapeHTML(gamif.porcentaje_nivel)}" aria-valuemin="0" aria-valuemax="100">
                        <div class="gamif-xp-fill" style="width: ${escapeHTML(gamif.porcentaje_nivel)}%;"></div>
                    </div>
                </div>
            </div>`;

        const ultima = planta.ultima_medicion;
        renderUltimaMedicion(ultima);
        const claveEspecie = (planta.especie || '').trim().toLowerCase();
        const cuidados = CARE_TIPS[claveEspecie] || [
            'Revisa la humedad ambiental y la ventilación del espacio.',
            'Consulta los rangos de luz y temperatura de esta especie.',
            'Mantén un buen drenaje para evitar exceso de agua.',
        ];
        document.getElementById('cuidados-especie').innerHTML = cuidados.map((tip) => `<li>${escapeHTML(tip)}</li>`).join('');
        const btnConectar = document.getElementById('btn-conectar');
        if (btnConectar) {
            btnConectar.textContent = planta.dispositivo_conectado
                ? 'Gestionar dispositivo'
                : 'Conectar dispositivo';
        }
    } catch (error) {
        perfil.className = 'inline-error';
        perfil.textContent = error.message;
    }
}

function resumenDiagnostico(medicion) {
    if (medicion.estado_general === 'INDETERMINADO') {
        return 'No hay parámetros evaluables suficientes para determinar el estado de la planta.';
    }
    const fueraDeRango = Object.entries(medicion.detalle_parametros || {})
        .filter(([, estado]) => estado !== 'OPTIMO')
        .map(([parametro]) => PARAMETER_LABELS[parametro] || parametro.toLowerCase());
    if (!fueraDeRango.length) return 'Todas las lecturas están dentro del rango ideal.';
    if (fueraDeRango.length === 1 && fueraDeRango[0].startsWith('Humedad')) return 'Tu planta necesita atención con el agua.';
    return `Revisa: ${fueraDeRango.join(', ')}.`;
}

async function cargarHistorial() {
    const contenedor = document.getElementById('contenedor-historial');
    if (!appState.plantId) {
        contenedor.innerHTML = '<p class="inline-error">Selecciona una planta para ver su historial.</p>';
        return;
    }
    contenedor.innerHTML = '<p class="loading-message">Cargando historial…</p>';
    try {
        const historial = await API.getHistory(appState.plantId);
        if (!historial.length) {
            renderVacio(contenedor, 'Todavía no hay historial', 'Cuando tu matera registre lecturas, las verás aquí.');
            return;
        }
        contenedor.innerHTML = historial.map((medicion) => {
            const estado = medicion.estado_general || 'INDETERMINADO';
            const valores = Object.entries(medicion.valores || {}).map(([parametro, valor]) =>
                `<span>${escapeHTML(PARAMETER_LABELS[parametro] || parametro)}: <strong>${escapeHTML(valorConUnidad(parametro, valor))}</strong></span>`
            ).join('');
            return `
                <article class="history-card">
                    <div class="history-card-heading">
                        <time>${new Date(medicion.fecha).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}</time>
                        <span class="status-pill ${claseEstado(estado)}">${traducirEstado(estado)}</span>
                    </div>
                    <p class="history-summary">${escapeHTML(resumenDiagnostico(medicion))}</p>
                    <div class="history-values">${valores}</div>
                </article>`;
        }).join('');
    } catch (error) {
        contenedor.innerHTML = `<p class="inline-error">${escapeHTML(error.message)}</p>`;
    }
}

function problemaParametro(parametro, estado) {
    const nombres = {
        temperatura: [
            ['La temperatura está por debajo de lo ideal.', 'El frío prolongado puede ralentizar su crecimiento.'],
            ['La temperatura está por encima de lo ideal.', 'El calor excesivo puede deshidratar sus hojas.'],
        ],
        humedad: [
            ['El sustrato está más seco de lo recomendado.', 'Si se mantiene así, la planta puede marchitarse.'],
            ['El sustrato tiene exceso de humedad.', 'El exceso de agua puede afectar las raíces.'],
        ],
        luz: [
            ['La planta recibe poca luz.', 'Con poca luz puede crecer más lentamente.'],
            ['La planta recibe más luz de la recomendada.', 'La luz intensa directa puede dañar sus hojas.'],
        ],
    };
    const descripciones = nombres[parametro];
    if (!descripciones) return null;
    const indice = estado === 'BAJO' ? 0 : estado === 'ALTO' ? 1 : -1;
    if (indice < 0) return null;
    return {
        titulo: `${PARAMETER_LABELS[parametro] || parametro}: ${traducirEstado(estado).toLowerCase()}`,
        descripcion: descripciones[indice][0],
        consecuencia: descripciones[indice][1],
    };
}

async function cargarDiagnostico() {
    const contenedor = document.getElementById('contenido-diagnostico');
    contenedor.innerHTML = '<p class="loading-message">Preparando el diagnóstico…</p>';
    if (!appState.plantId) {
        renderVacio(contenedor, 'Selecciona una planta', 'Vuelve a tus plantas y abre el detalle para ver su diagnóstico.');
        return;
    }
    try {
        const planta = await API.getPlant(appState.plantId);
        appState.plant = planta;
        const medicion = planta.ultima_medicion;
        if (!medicion) {
            renderVacio(contenedor, 'Aún no hay diagnóstico', 'Esperamos la primera medición del ESP32. El botón muestra el último diagnóstico recibido y no solicita una nueva lectura.');
            return;
        }
        const estado = medicion.estado_general || 'INDETERMINADO';
        const indeterminado = estado === 'INDETERMINADO';
        const problemas = Object.entries(medicion.detalle_parametros || {})
            .map(([parametro, estadoParametro]) => problemaParametro(parametro, estadoParametro))
            .filter(Boolean);
        contenedor.innerHTML = `
            <section class="diagnosis-summary ${claseEstado(estado)}">
                <span class="diagnosis-plant-icon" aria-hidden="true">🪴</span>
                <p class="eyebrow">ESTADO ACTUAL</p>
                <h2>${traducirEstado(estado)}</h2>
                <p>${escapeHTML(resumenDiagnostico(medicion))}</p>
                <time>${new Date(medicion.fecha).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })}</time>
            </section>
            <section class="diagnosis-section">
                <h2>${indeterminado ? 'Datos insuficientes' : problemas.length ? 'Qué observamos' : '¡Va muy bien!'}</h2>
                ${problemas.length
                    ? `<div class="problem-list">${problemas.map((problema) => `<article class="problem-card"><span class="problem-mark" aria-hidden="true">!</span><div><h3>${escapeHTML(problema.titulo)}</h3><p>${escapeHTML(problema.descripcion)}</p><p class="problem-consequence"><strong>Si continúa:</strong> ${escapeHTML(problema.consecuencia)}</p></div></article>`).join('')}</div>`
                    : indeterminado
                        ? '<p class="muted">No se puede confirmar si la planta está saludable. Verifica los sensores y espera una medición completa.</p>'
                        : '<p class="muted">Todas las mediciones disponibles están en su rango ideal.</p>'}
            </section>
            <section class="diagnosis-section">
                <h2>Qué puedes hacer</h2>
                ${medicion.recomendaciones?.length
                    ? `<ul class="recommendation-list">${medicion.recomendaciones.map((item) => `<li>${escapeHTML(item)}</li>`).join('')}</ul>`
                    : indeterminado
                        ? '<p class="muted">Comprueba que todos los sensores estén enviando valores válidos.</p>'
                        : '<p class="success-note">Continúa con sus cuidados habituales y revisa las próximas mediciones.</p>'}
            </section>`;
    } catch (error) {
        contenedor.innerHTML = `<p class="inline-error">${escapeHTML(error.message)}</p>`;
    }
}

function manejarMedicionEnVivo(evento) {
    if (!evento || evento.tipo !== 'medicion' || !evento.medicion) return;

    const plantaId = String(evento.planta_id);
    const pantalla = document.querySelector('.pantalla.activa')?.id.replace('pantalla-', '');
    if (pantalla === 'mis-plantas') cargarPlantas();

    if (String(appState.plantId) !== plantaId) return;
    if (appState.plant) appState.plant.ultima_medicion = evento.medicion;

    if (pantalla === 'detalles') renderUltimaMedicion(evento.medicion);
    if (pantalla === 'historial') cargarHistorial();
    if (pantalla === 'diagnostico') cargarDiagnostico();
}

function desconectarMedicionesEnVivo() {
    window.clearTimeout(socketReintento);
    window.clearInterval(socketHeartbeat);
    socketReintento = null;
    socketHeartbeat = null;
    if (medicionesSocket) {
        medicionesSocket.close();
        medicionesSocket = null;
    }
}

function conectarMedicionesEnVivo() {
    if (!API.getToken() || typeof WebSocket === 'undefined') return;
    if (medicionesSocket && [WebSocket.CONNECTING, WebSocket.OPEN].includes(medicionesSocket.readyState)) return;

    const url = new URL('/api/v1/ws/mediciones', CONFIG.API_BASE_URL);
    url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
    const socket = new WebSocket(url);
    medicionesSocket = socket;

    socket.addEventListener('open', () => {
        const token = API.getToken();
        if (!token) {
            socket.close();
            return;
        }
        socket.send(JSON.stringify({ token }));
    });

    socket.addEventListener('message', (mensaje) => {
        let evento;
        try {
            evento = JSON.parse(mensaje.data);
        } catch (error) {
            console.error('El servidor envió un mensaje WebSocket inválido.', error);
            socket.close(1002, 'Mensaje inválido');
            return;
        }

        if (evento.tipo === 'autenticado') {
            socketHeartbeat = window.setInterval(() => {
                if (socket.readyState === WebSocket.OPEN) socket.send('ping');
            }, 15000);
        } else if (evento.tipo === 'medicion') {
            manejarMedicionEnVivo(evento);
        } else if (evento.tipo === 'error') {
            API.logout();
            window.dispatchEvent(new Event('sessionexpired'));
        }
    });

    socket.addEventListener('close', (evento) => {
        window.clearInterval(socketHeartbeat);
        socketHeartbeat = null;
        if (medicionesSocket === socket) medicionesSocket = null;
        if (evento.code === 1008 && API.getToken()) {
            API.logout();
            window.dispatchEvent(new Event('sessionexpired'));
            return;
        }
        if (API.getToken()) {
            socketReintento = window.setTimeout(conectarMedicionesEnVivo, 3000);
        }
    });

    socket.addEventListener('error', () => socket.close());
}

async function cargarEspecies() {
    const select = document.getElementById('planta-especie');
    if (select.dataset.loaded === 'true') return;
    select.innerHTML = '<option value="">Cargando especies…</option>';
    try {
        const especies = await API.getSpecies();
        select.innerHTML = '<option value="">Selecciona una especie</option>' +
            especies.map(({ especie }) => {
                const nombreLimpio = escapeHTML(especie);
                const nombreFormateado = escapeHTML(especie.charAt(0).toUpperCase() + especie.slice(1));
                return `<option value="${nombreLimpio}">${nombreFormateado}</option>`;
            }).join('');
        select.dataset.loaded = 'true';
    } catch (error) {
        select.innerHTML = '<option value="">No se pudieron cargar las especies</option>';
        mostrarToast(error.message, 'error');
    }
}

function cargarAjustes() {
    document.getElementById('ajustes-email').textContent =
        localStorage.getItem('usuario_email') || 'Tu cuenta PlantTech';
}

function mostrarErrorFormulario(formulario, mensaje) {
    let error = formulario.querySelector('.form-error');
    if (!error) {
        error = document.createElement('p');
        error.className = 'form-error';
        error.setAttribute('role', 'alert');
        formulario.prepend(error);
    }
    error.textContent = mensaje;
}

function limpiarErrorFormulario(formulario) {
    formulario.querySelector('.form-error')?.remove();
}

const minigameState = {
    activo: false,
    puntaje: 0,
    tiempo: 20,
    intervaloTiempo: null,
    intervaloSpawn: null,
};

function detenerMinijuego() {
    minigameState.activo = false;
    window.clearInterval(minigameState.intervaloTiempo);
    window.clearInterval(minigameState.intervaloSpawn);
    const tablero = document.getElementById('mg-tablero');
    if (tablero) tablero.innerHTML = '';
}

function prepararMinijuego() {
    if (!appState.plantId) {
        mostrarPantalla('mis-plantas');
        return;
    }
    detenerMinijuego();
    document.getElementById('mg-tiempo').textContent = '20';
    document.getElementById('mg-puntaje').textContent = '0';
    document.getElementById('mg-resultado').hidden = true;
    const btn = document.getElementById('btn-iniciar-mg');
    btn.disabled = false;
    btn.textContent = 'Empezar partida';
}

function mostrarFeedbackMinijuego(tablero, xPorcentaje, yPx, puntos) {
    const tag = document.createElement('span');
    tag.className = `mg-feedback ${puntos >= 0 ? 'positivo' : 'negativo'}`;
    tag.textContent = puntos >= 0 ? `+${puntos}` : `${puntos}`;
    tag.style.left = `${xPorcentaje}%`;
    tag.style.top = `${Math.max(12, yPx)}px`;
    tablero.appendChild(tag);
    window.setTimeout(() => tag.remove(), 550);
}

function crearElementoMinijuego() {
    if (!minigameState.activo) return;
    const tablero = document.getElementById('mg-tablero');

    // Probabilidades: 35% agua, 35% sol, 22% plaga, 8% abono brillante (+20 pts)
    const r = Math.random();
    let item;
    if (r < 0.35) {
        item = { emoji: '💧', puntos: 10, factorVelocidad: 1.0 };
    } else if (r < 0.70) {
        item = { emoji: '☀️', puntos: 10, factorVelocidad: 1.0 };
    } else if (r < 0.92) {
        item = { emoji: '🐛', puntos: -15, factorVelocidad: 0.9 };
    } else {
        item = { emoji: '✨', puntos: 20, factorVelocidad: 0.75 };
    }

    // Dificultad progresiva: conforme baja el tiempo, caen más rápido
    const progreso = (20 - minigameState.tiempo) / 20; // de 0.0 a 1.0
    const duracionBase = 1.35 - (progreso * 0.45);     // de 1.35s baja hasta 0.90s
    const variacion = (Math.random() * 0.25) - 0.1;
    const duracionSeg = Math.max(0.65, (duracionBase + variacion) * item.factorVelocidad);

    const posX = 6 + Math.random() * 78;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'mg-item';
    btn.textContent = item.emoji;
    btn.style.left = `${posX}%`;
    btn.style.setProperty('--duracion', `${duracionSeg.toFixed(2)}s`);

    btn.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        if (!minigameState.activo) return;
        const rectTablero = tablero.getBoundingClientRect();
        const rectBtn = btn.getBoundingClientRect();
        minigameState.puntaje = Math.max(0, minigameState.puntaje + item.puntos);
        document.getElementById('mg-puntaje').textContent = String(minigameState.puntaje);
        mostrarFeedbackMinijuego(tablero, posX, rectBtn.top - rectTablero.top, item.puntos);
        btn.remove();
    });

    tablero.appendChild(btn);
    window.setTimeout(() => btn.remove(), Math.ceil(duracionSeg * 1000) + 100);
}

function iniciarMinijuego() {
    prepararMinijuego();
    minigameState.activo = true;
    minigameState.puntaje = 0;
    minigameState.tiempo = 20;
    document.getElementById('btn-iniciar-mg').disabled = true;

    crearElementoMinijuego();
    minigameState.intervaloSpawn = window.setInterval(crearElementoMinijuego, 360);
    minigameState.intervaloTiempo = window.setInterval(() => {
        minigameState.tiempo -= 1;
        document.getElementById('mg-tiempo').textContent = String(minigameState.tiempo);
        if (minigameState.tiempo <= 0) finalizarMinijuego();
    }, 1000);
}

async function finalizarMinijuego() {
    const puntajeFinal = minigameState.puntaje;
    detenerMinijuego();
    const resBox = document.getElementById('mg-resultado');
    const btn = document.getElementById('btn-iniciar-mg');
    resBox.hidden = false;
    resBox.innerHTML = '<p class="loading-message">Guardando experiencia…</p>';

    try {
        const res = await API.playMinigame(appState.plantId, puntajeFinal);
        const msgTope = res.tope_diario_alcanzado
            ? '<p class="muted">Alcanzaste el límite diario de XP por minijuego. ¡Vuelve mañana!</p>'
            : `<p class="muted">Aún puedes ganar ${escapeHTML(res.xp_restante_hoy)} XP hoy jugando.</p>`;
        resBox.innerHTML = `
            <h3>¡Partida terminada!</h3>
            <p>Puntaje: <strong>${escapeHTML(puntajeFinal)}</strong> · Ganaste <strong>+${escapeHTML(res.xp_ganada)} XP</strong></p>
            <p>Nivel actual: <strong>${escapeHTML(res.gamificacion.nivel)}</strong> (${escapeHTML(res.gamificacion.xp_nivel_actual)}/${escapeHTML(res.gamificacion.xp_siguiente_nivel)} XP)</p>
            ${msgTope}`;
    } catch (error) {
        resBox.innerHTML = `<p class="inline-error">${escapeHTML(error.message)}</p>`;
    } finally {
        btn.disabled = false;
        btn.textContent = 'Jugar de nuevo';
    }
}

async function cargarConectarDispositivo() {
    if (!appState.plantId) {
        mostrarPantalla('mis-plantas');
        return;
    }

    const btnDesvincular = document.getElementById('btn-desvincular-dispositivo');
    const titulo = document.getElementById('conectar-estado-titulo');
    const texto = document.getElementById('conectar-estado-texto');
    const estadoQR = document.getElementById('qr-estado');
    const btnEscanear = document.getElementById('btn-escanear-qr');
    const btnCancelar = document.getElementById('btn-cancelar-vinculacion');
    detenerCamaraQR();
    qrPairingSessionId = null;
    btnEscanear.disabled = false;
    btnCancelar.hidden = true;
    estadoQR.textContent = 'Mantén presionado el botón BOOT del ESP32 durante 5 segundos y escanea el QR de su pantalla.';

    try {
        const planta = await API.getPlant(appState.plantId);
        appState.plant = planta;
        const conectado = Boolean(planta.dispositivo_conectado);

        titulo.textContent = conectado ? '● Dispositivo vinculado' : '○ Sin dispositivo vinculado';
        texto.textContent = conectado
            ? 'Esta planta ya tiene un ESP32 conectado. Para volver a vincularlo, mantén presionado BOOT durante 5 segundos; tras escanear, confirma en el dispositivo durante 2 segundos.'
            : 'Mantén presionado el botón BOOT del ESP32 durante 5 segundos y escanea el QR que aparece en su pantalla.';
        btnDesvincular.hidden = !conectado;
    } catch (error) {
        mostrarToast(error.message, 'error');
    }
}

function detenerCamaraQR() {
    window.clearTimeout(qrScanTimer);
    qrScanTimer = null;
    if (qrStream) {
        qrStream.getTracks().forEach((track) => track.stop());
        qrStream = null;
    }
    const video = document.getElementById('qr-camera');
    if (video) {
        video.pause();
        video.srcObject = null;
        video.hidden = true;
    }
}

async function cancelarVinculacionQR(mostrarEstado = true) {
    const sesionId = qrPairingSessionId;
    const plantaId = appState.plantId;
    qrPairingSessionId = null;
    qrPairingAttempt += 1;
    detenerCamaraQR();

    document.getElementById('btn-escanear-qr').disabled = false;
    document.getElementById('btn-cancelar-vinculacion').hidden = true;
    if (sesionId && plantaId) {
        try {
            await API.cancelDevicePairing(plantaId, sesionId);
        } catch (error) {
            mostrarToast(`No se pudo cancelar la vinculacion: ${error.message}`, 'error');
        }
    }
    if (mostrarEstado) {
        document.getElementById('qr-estado').textContent =
            'Vinculacion cancelada. El codigo temporal ya no podra usarse.';
    }
}

function decodificarQRVinculacion(valor) {
    const coincidencia = /^PT1:([a-fA-F0-9]{24}):([a-fA-F0-9]{32})$/.exec(valor.trim());
    if (!coincidencia) {
        throw new Error('El QR no corresponde a una solicitud de vinculacion PlantTech.');
    }
    return {
        dispositivoId: coincidencia[1].toLowerCase(),
        codigo: coincidencia[2].toLowerCase(),
    };
}

async function esperarConfirmacionVinculacion(plantaId, sesionId, intento) {
    while (intento === qrPairingAttempt) {
        const estado = await API.getDevicePairing(plantaId, sesionId);
        if (intento !== qrPairingAttempt) return;
        if (estado.estado === 'completada') {
            qrPairingSessionId = null;
            qrPairingAttempt += 1;
            detenerCamaraQR();
            document.getElementById('btn-escanear-qr').disabled = false;
            document.getElementById('btn-cancelar-vinculacion').hidden = true;
            document.getElementById('qr-estado').textContent = 'Dispositivo vinculado correctamente.';
            mostrarToast('Dispositivo vinculado correctamente.', 'success');
            mostrarPantalla('detalles');
            return;
        }
        if (estado.estado === 'expirada') {
            throw new Error('El codigo temporal expiro. Vuelve a escanear el QR del ESP32.');
        }
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
    }
}

async function procesarQRVinculacion(valor, intento) {
    detenerCamaraQR();
    const btnEscanear = document.getElementById('btn-escanear-qr');
    const estadoQR = document.getElementById('qr-estado');
    btnEscanear.disabled = true;

    try {
        const datosQR = decodificarQRVinculacion(valor);
        estadoQR.textContent = 'QR leído. Confirma la solicitud en el ESP32 manteniendo BOOT durante 2 segundos.';
        const solicitud = await API.linkDevice(
            appState.plantId,
            datosQR.dispositivoId,
            datosQR.codigo
        );
        if (intento !== qrPairingAttempt) {
            try {
                await API.cancelDevicePairing(appState.plantId, solicitud.sesion_id);
            } catch (error) {
                mostrarToast(`No se pudo cancelar la vinculacion: ${error.message}`, 'error');
            }
            return;
        }
        qrPairingSessionId = solicitud.sesion_id;
        await esperarConfirmacionVinculacion(appState.plantId, solicitud.sesion_id, intento);
    } catch (error) {
        if (intento === qrPairingAttempt) {
            estadoQR.textContent = error.message;
            btnEscanear.disabled = false;
            document.getElementById('btn-cancelar-vinculacion').hidden = true;
            qrPairingSessionId = null;
            qrPairingAttempt += 1;
        }
    }
}

async function iniciarEscaneoQR() {
    const estadoQR = document.getElementById('qr-estado');
    const btnEscanear = document.getElementById('btn-escanear-qr');
    const btnCancelar = document.getElementById('btn-cancelar-vinculacion');
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
        estadoQR.textContent = 'La camara requiere una conexion segura HTTPS o localhost.';
        return;
    }
    if (!('BarcodeDetector' in window)) {
        estadoQR.textContent = 'Este navegador no incluye lector QR. Prueba con Chrome o Edge actualizado.';
        return;
    }

    const intento = ++qrPairingAttempt;
    btnEscanear.disabled = true;
    btnCancelar.hidden = false;
    estadoQR.textContent = 'Apunta la camara al QR que muestra el ESP32.';
    try {
        const detector = new BarcodeDetector({ formats: ['qr_code'] });
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: { ideal: 'environment' } },
            audio: false,
        });
        if (intento !== qrPairingAttempt) {
            stream.getTracks().forEach((track) => track.stop());
            return;
        }
        qrStream = stream;
        const video = document.getElementById('qr-camera');
        video.srcObject = qrStream;
        video.hidden = false;
        await video.play();
        if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
            await new Promise((resolve) => {
                video.addEventListener('loadeddata', resolve, { once: true });
            });
        }

        const buscarQR = async () => {
            if (intento !== qrPairingAttempt) return;
            try {
                const codigos = await detector.detect(video);
                if (codigos.length) {
                    await procesarQRVinculacion(codigos[0].rawValue, intento);
                    return;
                }
            } catch (error) {
                if (intento === qrPairingAttempt) {
                    estadoQR.textContent = `No se pudo leer el QR: ${error.message}`;
                    await cancelarVinculacionQR(false);
                }
                return;
            }
            qrScanTimer = window.setTimeout(buscarQR, 250);
        };
        await buscarQR();
    } catch (error) {
        if (intento === qrPairingAttempt) {
            detenerCamaraQR();
            btnEscanear.disabled = false;
            btnCancelar.hidden = true;
            estadoQR.textContent = `No se pudo iniciar la camara: ${error.message}`;
        }
    }
}

function configurarEventos() {
    document.addEventListener('click', (evento) => {
        const navegacion = evento.target.closest('[data-screen]');
        if (navegacion) {
            mostrarPantalla(navegacion.dataset.screen);
            return;
        }
        const tarjeta = evento.target.closest('[data-plant-id]');
        if (tarjeta) {
            appState.plantId = tarjeta.dataset.plantId;
            mostrarPantalla('detalles');
            return;
        }
        if (evento.target.closest('[data-retry="plants"]')) cargarPlantas();
    });

    document.getElementById('form-login').addEventListener('submit', async (evento) => {
        evento.preventDefault();
        const form = evento.currentTarget;
        limpiarErrorFormulario(form);
        const submit = form.querySelector('[type="submit"]');
        submit.disabled = true;
        try {
            await API.login(document.getElementById('email').value.trim(), document.getElementById('password').value);
            conectarMedicionesEnVivo();
            mostrarPantalla('mis-plantas');
        } catch (error) {
            mostrarErrorFormulario(form, error.message);
        } finally {
            submit.disabled = false;
        }
    });

    document.getElementById('form-registro').addEventListener('submit', async (evento) => {
        evento.preventDefault();
        const form = evento.currentTarget;
        limpiarErrorFormulario(form);
        const password = document.getElementById('registro-password').value;
        const confirmacion = document.getElementById('registro-confirmar').value;
        if (password !== confirmacion) {
            mostrarErrorFormulario(form, 'Las contraseñas no coinciden.');
            return;
        }
        const submit = form.querySelector('[type="submit"]');
        submit.disabled = true;
        try {
            await API.register(
                document.getElementById('registro-nombre').value.trim(),
                document.getElementById('registro-email').value.trim(),
                password,
            );
            document.getElementById('email').value = document.getElementById('registro-email').value.trim();
            form.reset();
            mostrarToast('Cuenta creada. Ya puedes iniciar sesión.', 'success');
            mostrarPantalla('login');
        } catch (error) {
            mostrarErrorFormulario(form, error.message);
        } finally {
            submit.disabled = false;
        }
    });

    document.getElementById('btn-olvide-contrasena').addEventListener('click', () => {
        mostrarToast('La recuperación de contraseña estará disponible próximamente.', 'info');
    });
    document.getElementById('btn-opciones').addEventListener('click', (evento) => {
        const menu = document.getElementById('menu-desplegable');
        menu.hidden = !menu.hidden;
        evento.currentTarget.setAttribute('aria-expanded', String(!menu.hidden));
    });
    document.getElementById('btn-ver-historial').addEventListener('click', () => {
        document.getElementById('menu-desplegable').hidden = true;
        mostrarPantalla('historial');
    });
    document.getElementById('btn-borrar-planta').addEventListener('click', async () => {
        document.getElementById('menu-desplegable').hidden = true;
        if (!appState.plantId || !window.confirm('¿Quieres borrar esta planta y todo su historial? Esta acción no se puede deshacer.')) return;
        try {
            await API.deletePlant(appState.plantId);
            appState.plantId = null;
            appState.plant = null;
            mostrarToast('La planta se eliminó correctamente.', 'success');
            mostrarPantalla('mis-plantas');
        } catch (error) {
            mostrarToast(error.message, 'error');
        }
    });
    document.getElementById('btn-diagnosticar').addEventListener('click', () => {
        mostrarPantalla('diagnostico');
    });
    document.getElementById('btn-conectar').addEventListener('click', () => {
        mostrarPantalla('conectar');
    });

    document.getElementById('btn-escanear-qr').addEventListener('click', iniciarEscaneoQR);
    document.getElementById('btn-cancelar-vinculacion').addEventListener(
        'click',
        () => cancelarVinculacionQR()
    );

    document.getElementById('btn-desvincular-dispositivo').addEventListener('click', async () => {
        if (!appState.plantId || !window.confirm('¿Desvincular el ESP32 de esta planta? Dejará de recibir mediciones.')) return;
        try {
            await API.unlinkDevice(appState.plantId);
            mostrarToast('Dispositivo desvinculado.', 'success');
            mostrarPantalla('detalles');
        } catch (error) {
            mostrarToast(error.message, 'error');
        }
    });
    document.getElementById('btn-jugar-minijuego').addEventListener('click', () => {
        mostrarPantalla('minijuego');
    });
    document.getElementById('btn-iniciar-mg').addEventListener('click', iniciarMinijuego);
    
    document.getElementById('form-planta').addEventListener('submit', async (evento) => {
        evento.preventDefault();
        const form = evento.currentTarget;
        limpiarErrorFormulario(form);
        const submit = form.querySelector('[type="submit"]');
        submit.disabled = true;
        try {
            const planta = await API.createPlant({
                apodo: document.getElementById('planta-apodo').value.trim(),
                especie: document.getElementById('planta-especie').value,
            });
            appState.plantId = planta.id;
            appState.plant = planta;
            form.reset();
            document.getElementById('planta-especie').dataset.loaded = 'true';
            mostrarToast('Tu planta se añadió correctamente.', 'success');
            mostrarPantalla('detalles');
        } catch (error) {
            mostrarErrorFormulario(form, error.message);
        } finally {
            submit.disabled = false;
        }
    });
    document.getElementById('btn-cerrar-sesion').addEventListener('click', () => {
        API.logout();
        desconectarMedicionesEnVivo();
        appState.plantId = null;
        appState.plant = null;
        mostrarPantalla('bienvenida');
    });
    document.addEventListener('click', (evento) => {
        const menu = document.getElementById('menu-desplegable');
        if (!evento.target.closest('.menu-wrap') && menu && !menu.hidden) {
            menu.hidden = true;
            document.getElementById('btn-opciones').setAttribute('aria-expanded', 'false');
        }
    });
    window.addEventListener('sessionexpired', () => {
        desconectarMedicionesEnVivo();
        appState.plantId = null;
        appState.plant = null;
        mostrarPantalla('bienvenida');
        mostrarToast('Tu sesión expiró. Inicia sesión de nuevo.', 'error');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    configurarEventos();
    if (API.getToken()) {
        conectarMedicionesEnVivo();
        const guardada = localStorage.getItem('pantalla_actual');
        mostrarPantalla(guardada && !['bienvenida', 'login', 'registro'].includes(guardada) ? guardada : 'mis-plantas');
    } else {
        mostrarPantalla('bienvenida');
    }
});
