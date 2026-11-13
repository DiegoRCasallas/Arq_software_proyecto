const appState = {
    plantId: null,
    plant: null,
    plants: [],
    toastTimer: null,
};

const PARAMETER_LABELS = {
    temperatura: 'Temperatura',
    humedad: 'Humedad del suelo (agua)',
    luz: 'Luz',
};

const CARE_TIPS = {
    cinta: [
        'Riega cuando la capa superior del sustrato empiece a secarse.',
        'Prefiere luz indirecta y espacios bien iluminados.',
        'Evita dejar agua acumulada en la maceta.',
    ],
    albahaca: [
        'Requiere al menos 6 horas de luz solar o iluminación muy brillante.',
        'Mantén el sustrato húmedo con buen drenaje, sin encharcar.',
        'Poda los brotes florales para estimular hojas frescas y densas.',
    ],
    poto: [
        'Tolera bien luz indirecta moderada y sombra parcial.',
        'Deja secar ligeramente la capa superior de tierra entre riegos.',
        'Limpia sus hojas ocasionalmente para mejorar la absorción de luz.',
    ],
    suculenta: [
        'Riega de forma espaciada, permitiendo que la tierra se seque por completo.',
        'Ubícala en un lugar con abundante luz directa para mantener su color.',
        'Usa macetas con buen drenaje para proteger sus raíces.',
    ],
    helecho: [
        'Mantén el sustrato uniformemente húmedo, sin permitir que se seque del todo.',
        'Prefiere luz suave filtrada o semisombra; evita el sol directo.',
        'Agradece la humedad ambiental; pulveriza agua cerca de sus frondas.',
    ],
    orquidea: [
        'Riega por inmersión semanalmente y escurre todo el exceso de agua.',
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

    document.querySelectorAll('.pantalla').forEach((pantalla) => {
        pantalla.classList.toggle('activa', pantalla.id === `pantalla-${idActiva}`);
    });

    const nav = document.getElementById('menu-inferior');
    const esPantallaAcceso = ['bienvenida', 'login', 'registro'].includes(idActiva);
    const navVisible = Boolean(API.getToken()) && !esPantallaAcceso && idActiva !== 'diagnostico';
    nav.hidden = !navVisible;
    document.body.classList.toggle('diagnosis-active', idActiva === 'diagnostico');
    document.querySelectorAll('.nav-item').forEach((item) => {
        item.classList.toggle('active', item.dataset.screen === idActiva);
    });

    localStorage.setItem('pantalla_actual', idActiva);
    if (idActiva === 'mis-plantas') cargarPlantas();
    if (idActiva === 'detalles') cargarDetalles();
    if (idActiva === 'historial') cargarHistorial();
    if (idActiva === 'diagnostico') cargarDiagnostico();
    if (idActiva === 'add-planta') cargarEspecies();
    if (idActiva === 'ajustes') cargarAjustes();
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
                        <span class="plant-species">${escapeHTML(planta.especie)}</span>
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
        perfil.className = 'detail-profile';
        perfil.innerHTML = `
            <div class="large-plant-avatar" aria-hidden="true">🪴</div>
            <div class="detail-profile-copy">
                <span class="eyebrow">${escapeHTML(planta.especie)}</span>
                <h2>${escapeHTML(planta.apodo || planta.especie)}</h2>
                <span class="connection-note ${planta.dispositivo_conectado ? 'connected' : ''}">${planta.dispositivo_conectado ? '● Dispositivo conectado' : '○ Dispositivo pendiente de conexión'}</span>
            </div>`;

        const ultima = planta.ultima_medicion;
        renderMediciones(document.getElementById('estado-actual'), ultima);
        renderRecomendaciones(document.getElementById('recomendaciones-actuales'), ultima);
        document.getElementById('fecha-medicion').textContent = ultima
            ? new Date(ultima.fecha).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' })
            : 'Sin datos';
        const claveEspecie = (planta.especie || '').trim().toLowerCase();
        const cuidados = CARE_TIPS[claveEspecie] || [
            'Revisa la humedad del sustrato antes de regar.',
            'Consulta los rangos de luz y temperatura de esta especie.',
            'Mantén un buen drenaje para evitar exceso de agua.',
        ];
        document.getElementById('cuidados-especie').innerHTML = cuidados.map((tip) => `<li>${escapeHTML(tip)}</li>`).join('');
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
        mostrarToast('La conexión de un dispositivo estará disponible próximamente.', 'info');
    });
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
        appState.plantId = null;
        appState.plant = null;
        mostrarPantalla('bienvenida');
        mostrarToast('Tu sesión expiró. Inicia sesión de nuevo.', 'error');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    configurarEventos();
    if (API.getToken()) {
        const guardada = localStorage.getItem('pantalla_actual');
        mostrarPantalla(guardada && !['bienvenida', 'login', 'registro'].includes(guardada) ? guardada : 'mis-plantas');
    } else {
        mostrarPantalla('bienvenida');
    }
});
