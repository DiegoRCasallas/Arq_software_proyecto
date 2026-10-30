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
│   ├── styles.css         # Estilos mobile-first del cliente web
│   └── index.html         # Cliente web estático
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
*Envía una medición cada 5 segundos. La mayoría son normales (`201`, SALUDABLE); el simulador mezcla a propósito casos anómalos (`201`, CRITICO), lecturas defectuosas como texto o `null` (`400 VALOR_NO_NUMERICO`) y valores físicamente imposibles (`400 VALOR_FUERA_DE_RANGO_FISICO`), para que veas cómo reacciona el backend.*

### 3. Ejecutar el Frontend
Abre el archivo `frontend/index.html` en tu navegador o usa Live Server en VS Code. El cliente usa `http://localhost:5000` al ejecutarse localmente y la URL de Railway en otros dominios. Para agregar una especie nueva, registra su perfil en la tabla de referencia.
* *Nota:* Si utilizas la extensión "Live Server" de VS Code, asegúrate de configurar `.vscode/settings.json` para ignorar los cambios en `*.db`, de lo contrario, la página se recargará cada 5 segundos cuando el simulador guarde datos.

> **¿Ya tenías una base de datos de una versión anterior?** Vuelve a ejecutar `python3 seed.py`: no duplica nada, solo sincroniza los rangos de la especie "Cinta" con los límites físicos actuales (antes eran límites de tolerancia y rechazarían lecturas anómalas legítimas). Como alternativa, borra `backend/instance/matera.db` y siembra de nuevo.

**Credenciales de prueba generadas por `seed.py`:**
* **Email:** `prueba@planttech.com`
* **Contraseña:** `12345`

## Endpoints Principales de la API (v1)

| Método | Ruta | Protegido (JWT) | Descripción |
|--------|------|-----------------|-------------|
| POST | `/api/v1/usuarios/registro` | No | Registra un nuevo usuario en la plataforma. |
| POST | `/api/v1/usuarios/login` | No | Autentica al usuario y devuelve el token JWT. |
| GET | `/api/v1/plantas` | Sí | Lista las plantas del usuario con su última medición y diagnóstico. |
| POST | `/api/v1/plantas` | Sí | Crea una planta asociada a una especie soportada. |
| GET | `/api/v1/plantas/<id>` | Sí | Consulta el detalle de una planta propia y su última lectura. |
| DELETE | `/api/v1/plantas/<id>` | Sí | Elimina una planta propia junto con su historial. |
| POST | `/api/v1/dispositivos/<id>/mediciones` | Token de dispositivo | Endpoint para el ESP32. Registra lecturas de sensores (ver contrato abajo). |
| GET | `/api/v1/plantas/<id>/historial` | Sí | Devuelve el historial de diagnósticos de una planta. |
| GET | `/api/v1/especies` | No | Lista las especies soportadas y sus rangos de referencia. |
| GET | `/health` | No | Verificación de disponibilidad del servicio. |

El frontend web es mobile-first e incluye bienvenida, registro/inicio de sesión, colección y detalle de plantas, historial y diagnóstico de la última medición. La pantalla de conexión del ESP32 y recuperación de contraseña se mantienen como funciones próximamente disponibles. Al eliminar una planta también se eliminan sus mediciones.

### Contrato de `POST /api/v1/dispositivos/<id>/mediciones`

Cabecera `X-Device-Token: <token>` y cuerpo `{"valores": {"temperatura": 22, "humedad": 50, "luz": 800}}`.
Una medición se acepta **completa o no se acepta**: si falla cualquier regla, no se guarda nada.

| Situación | HTTP | `error` |
|---|---|---|
| Medición válida (aunque la planta esté mal: se diagnostica) | 201 | — |
| Falta la cabecera `X-Device-Token` | 401 | `AUTORIZACION_DENEGADA` |
| Dispositivo inexistente **o** token incorrecto (misma respuesta a propósito, para no revelar qué dispositivos existen) | 401 | `DISPOSITIVO_NO_AUTORIZADO` |
| Cuerpo que no es JSON, o sin objeto `valores` no vacío | 400 | `PARAMETRO_AUSENTE` |
| Valor `null`, texto no numérico, booleano, `NaN` o infinito | 400 | `VALOR_NO_NUMERICO` |
| Parámetro que la especie no define (p. ej. `ph`) | 400 | `PARAMETRO_DESCONOCIDO` |
| Falta un parámetro que la especie sí define | 400 | `PARAMETRO_AUSENTE` |
| Valor fuera de `[minimo, maximo]` del rango (físicamente imposible) | 400 | `VALOR_FUERA_DE_RANGO_FISICO` |
| Error inesperado del servidor | 500 | `ERROR_INTERNO` |

Cada rango de referencia tiene cuatro límites: `minimo`/`maximo` son los **límites físicos** del parámetro (fuera de ellos la lectura se rechaza), y `optimo_min`/`optimo_max` son el rango ideal (fuera de él la planta queda BAJO/ALTO). Estado general: sin parámetros evaluables → `INDETERMINADO`; 0 fuera del óptimo → `SALUDABLE`; 1 → `EN_RIESGO`; 2 o más → `CRITICO`.

Persistencia de la tabla de referencia: variable `TIPO_PERSISTENCIA=SQL` (por defecto) o `CSV` (lee `backend/infraestructura/persistencia/especies.csv`).

## Cómo ejecutar las pruebas (Testing)

```bash
cd backend
source venv/bin/activate
pytest
```

Las pruebas usan una base SQLite temporal por test (no tocan `matera.db`) y cubren dominio, casos de uso (con repositorios falsos), adaptadores SQL/CSV y los endpoints de punta a punta.
