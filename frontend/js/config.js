/**
 * Configuración del cliente. Único lugar donde se define la URL base
 * del backend, para no repetirla ni "quemarla" (hardcodear) en cada
 * llamada fetch.
 */
const localHosts = new Set(['', 'localhost', '127.0.0.1']);
const CONFIG = {
    API_BASE_URL: localHosts.has(window.location.hostname)
        ? 'http://localhost:5000'
        : 'https://arqsoftwareproyecto-production.up.railway.app',
};
