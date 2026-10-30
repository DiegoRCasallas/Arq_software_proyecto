const API = (() => {
    const tokenKey = 'jwt_token';
    const baseUrl = `${CONFIG.API_BASE_URL.replace(/\/$/, '')}/api/v1`;

    function getToken() {
        return localStorage.getItem(tokenKey);
    }

    async function request(path, options = {}) {
        const headers = new Headers(options.headers || {});
        headers.set('Accept', 'application/json');
        if (options.body !== undefined) headers.set('Content-Type', 'application/json');
        const token = getToken();
        if (token) headers.set('Authorization', `Bearer ${token}`);

        let response;
        try {
            response = await fetch(`${baseUrl}${path}`, { ...options, headers });
        } catch {
            throw new Error('No fue posible conectar con PlantTech. Revisa tu conexión e inténtalo de nuevo.');
        }

        const body = await response.text();
        let data = {};
        if (body) {
            try {
                data = JSON.parse(body);
            } catch {
                throw new Error('El servidor devolvió una respuesta que no se pudo interpretar.');
            }
        }

        if (response.status === 401 && token) {
            localStorage.removeItem(tokenKey);
            localStorage.removeItem('usuario_email');
            window.dispatchEvent(new Event('sessionexpired'));
        }
        if (!response.ok) {
            throw new Error(data.mensaje || data.error || 'Ocurrió un error. Inténtalo de nuevo.');
        }
        return data;
    }

    return {
        getToken,
        logout() {
            localStorage.removeItem(tokenKey);
            localStorage.removeItem('usuario_email');
        },
        async login(email, contrasena) {
            const data = await request('/usuarios/login', {
                method: 'POST',
                body: JSON.stringify({ email, contrasena }),
            });
            localStorage.setItem(tokenKey, data.token);
            localStorage.setItem('usuario_email', email);
            return data;
        },
        register(nombre, email, contrasena) {
            return request('/usuarios/registro', {
                method: 'POST',
                body: JSON.stringify({ nombre, email, contrasena }),
            });
        },
        getPlants() {
            return request('/plantas');
        },
        getPlant(plantaId) {
            return request(`/plantas/${encodeURIComponent(plantaId)}`);
        },
        createPlant(planta) {
            return request('/plantas', {
                method: 'POST',
                body: JSON.stringify(planta),
            });
        },
        deletePlant(plantaId) {
            return request(`/plantas/${encodeURIComponent(plantaId)}`, { method: 'DELETE' });
        },
        getSpecies() {
            return request('/especies');
        },
        getHistory(plantaId) {
            return request(`/plantas/${encodeURIComponent(plantaId)}/historial?limite=50`);
        },
    };
})();
