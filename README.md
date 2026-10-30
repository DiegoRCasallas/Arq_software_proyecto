# PlantTech: Matera Inteligente (Fase 2)

PlantTech es una plataforma IoT orientada al cuidado de las plantas. Este núcleo de software se encarga de recibir lecturas de sensores de hardware (como el ESP32), procesarlas dinámicamente según la especie de la planta y ofrecer un diagnóstico en tiempo real al usuario mediante una interfaz web segura e interactiva.

## Arquitectura del Software

Este proyecto implementa estrictamente **Arquitectura Hexagonal (Puertos y Adaptadores)**. 
El corazón del sistema (Dominio y Casos de Uso) está completamente aislado de detalles técnicos. No depende de Flask, SQLAlchemy, ni de bases de datos específicas. La comunicación hacia el exterior se realiza mediante interfaces (`Protocol` en Python) inyectadas a través de un contenedor de dependencias.

**Regla de Dependencias:**
```text
Presentación (Flask/Web) → Aplicación (Casos de Uso) → Dominio (Reglas) ← Infraestructura (SQL/JWT/ESP32)
```

## Estructura del Proyecto

```text
Arq_software_proyecto/
├── backend/
│   ├── presentacion/      # Controladores REST (Flask), Autenticación JWT y DTOs
│   ├── aplicacion/        # Casos de uso (orquestación: Login, Registrar, Consultar Historial)
│   ├── dominio/           # Entidades dinámicas, valores, servicios de evaluación y puertos
│   ├── infraestructura/   # Adaptadores (SQLAlchemy, PyJWT, Contenedor de Inyección)
│   ├── app.py             # Configuración y punto de entrada de Flask
│   ├── seed.py            # Script para poblar la base de datos inicial
│   └── requirements.txt   # Dependencias de Python
├── frontend/
│   ├── js/                # Lógica JavaScript asíncrona (api.js, app.js)
│   └── index.html         # Cliente web estático maquetado según mockups
├── simulador_esp32.py     # Script para simular el envío de datos del sensor IoT
└── docs/                  # Documentos de arquitectura y diseño
```

## Requisitos del Sistema
* Python 3.9+
* Entorno virtual (venv)
* Navegador Web moderno

## Guía de Ejecución Local

Para probar el flujo completo (Backend + Base de Datos + Simulador + Frontend), sigue estos pasos abriendo **tres terminales distintas**:

### 1. Levantar el Backend y la Base de Datos
En la **Terminal 1**, prepara el entorno, puebla la base de datos de prueba y enciende el servidor:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Poblar la base de datos con un usuario y una planta de prueba
python3 seed.py

# Iniciar el servidor Flask
python3 app.py
```
*El servidor quedará disponible en `http://localhost:5000`.*

### 2. Iniciar el Hardware Simulado
En la **Terminal 2**, ejecuta el simulador que representa a la matera enviando mediciones de temperatura, humedad y luz:
```bash
# Desde la raíz del proyecto
python3 simulador_esp32.py
```
*Verás cómo envía peticiones cada 5 segundos y recibe respuestas `201 Created` con diagnósticos.*

### 3. Ejecutar el Frontend
Abre el archivo `frontend/index.html` en tu navegador web. 
* *Nota:* Si utilizas la extensión "Live Server" de VS Code, asegúrate de configurar `.vscode/settings.json` para ignorar los cambios en `*.db`, de lo contrario, la página se recargará cada 5 segundos cuando el simulador guarde datos.

**Credenciales de prueba generadas por `seed.py`:**
* **Email:** `prueba@planttech.com`
* **Contraseña:** `12345`

## Endpoints Principales de la API (v1)

| Método | Ruta | Protegido (JWT) | Descripción |
|--------|------|-----------------|-------------|
| POST | `/api/v1/usuarios/registro` | No | Registra un nuevo usuario en la plataforma. |
| POST | `/api/v1/usuarios/login` | No | Autentica al usuario y devuelve el token JWT. |
| POST | `/api/v1/dispositivos/<id>/mediciones` | No | Endpoint para el ESP32. Registra lecturas de sensores. |
| GET | `/api/v1/plantas/<id>/historial` | Sí | Devuelve el historial de diagnósticos de una planta. |
| GET | `/health` | No | Verificación de disponibilidad del servicio. |

## Cómo ejecutar las pruebas (Testing)

```bash
cd backend
source venv/bin/activate
pytest
```
