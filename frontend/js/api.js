const BASE_URL = 'http://localhost:5000/api/v1';

const API = {
    setToken: (token) => localStorage.setItem('jwt_token', token),
    getToken: () => localStorage.getItem('jwt_token'),
    logout: () => localStorage.removeItem('jwt_token'),
    
    getHeaders: function() {
        const headers = { 'Content-Type': 'application/json' };
        const token = this.getToken();
        if (token) headers['Authorization'] = `Bearer ${token}`; // Inyecta el JWT
        return headers;
    },

    login: async function(email, contrasena) {
        const res = await fetch(`${BASE_URL}/usuarios/login`, {
            method: 'POST',
            headers: this.getHeaders(),
            body: JSON.stringify({ email, contrasena })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.mensaje || 'Error en login');
        this.setToken(data.token);
        return data;
    },

    getHistorial: async function(plantaId) {
        const res = await fetch(`${BASE_URL}/plantas/${plantaId}/historial`, {
            method: 'GET',
            headers: this.getHeaders()
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.mensaje || 'Error al obtener historial');
        return data;
    }
};