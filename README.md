# Matera Inteligente — Núcleo de Diagnóstico

## Estructura

```
backend/
├── presentacion/     # Controladores REST y DTOs (Flask)
├── aplicacion/       # Casos de uso (orquestación)
├── dominio/          # Entidades, valores, servicios y puertos (sin dependencias externas)
├── infraestructura/  # Implementaciones concretas (CSV, config, Flask wiring)
└── tests/            # Pruebas unitarias, organizadas por capa
frontend/             # Cliente estático HTML/CSS/JS
docs/                 # Documento de arquitectura
```

## Cómo ejecutar el backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

El servidor queda disponible en `http://localhost:5000`.
Prueba rápida: `GET http://localhost:5000/health` → `{"status": "ok"}`.

## Cómo ejecutar las pruebas

```bash
cd backend
pytest
```

## Cómo ejecutar el frontend

El frontend es HTML/CSS/JS estático, servido por separado del backend (RA2).
Con el backend corriendo en `http://localhost:5000`, en otra terminal:

```bash
cd frontend
python3 -m http.server 8080
```

Abre `http://localhost:8080` en el navegador. Si tu backend corre en otro
host o puerto, ajusta `API_BASE_URL` en `frontend/config.js`.

## Endpoints planeados

| Método | Ruta          | Descripción                                  |
|--------|---------------|-----------------------------------------------|
| POST   | /diagnostico  | Evalúa una lectura y devuelve el diagnóstico  |
| GET    | /especies     | Lista las especies soportadas y sus rangos    |
| GET    | /health       | Verificación de disponibilidad del servicio   |

## Regla de dependencias

```
Presentación → Aplicación → Dominio ← Infraestructura
```

El dominio no importa nada de Flask, CSV, pandas ni ningún framework.
Se puede ejecutar y probar de forma completamente aislada.
