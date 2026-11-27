import json
import logging
from dataclasses import dataclass, field
from threading import Lock

from flask import Flask
from flask_sock import Sock
from simple_websocket.errors import ConnectionClosed

from infraestructura.config.contenedor import contenedor_app

logger = logging.getLogger(__name__)


@dataclass(eq=False)
class Conexion:
    websocket: object
    lock: Lock = field(default_factory=Lock)


class GestorConexiones:
    def __init__(self):
        self._lock = Lock()
        self._por_usuario = {}

    def registrar(self, usuario_id, websocket):
        conexion = Conexion(websocket)
        with self._lock:
            self._por_usuario.setdefault(usuario_id, []).append(conexion)
        return conexion

    def quitar(self, usuario_id, conexion):
        with self._lock:
            conexiones = self._por_usuario.get(usuario_id, [])
            if conexion in conexiones:
                conexiones.remove(conexion)
            if not conexiones:
                self._por_usuario.pop(usuario_id, None)

    def enviar(self, conexion, mensaje):
        try:
            with conexion.lock:
                conexion.websocket.send(mensaje)
        except (ConnectionClosed, OSError):
            return False
        return True

    def emitir(self, usuario_id, evento):
        mensaje = json.dumps(evento)
        with self._lock:
            conexiones = tuple(self._por_usuario.get(usuario_id, ()))

        for conexion in conexiones:
            if not self.enviar(conexion, mensaje):
                self.quitar(usuario_id, conexion)


gestor_conexiones = GestorConexiones()


def emitir_medicion(usuario_id, evento):
    gestor_conexiones.emitir(usuario_id, evento)


def _rechazar(websocket, mensaje):
    try:
        websocket.send(json.dumps({"tipo": "error", "mensaje": mensaje}))
        websocket.close(1008, mensaje)
    except (ConnectionClosed, OSError):
        pass


def registrar_websocket(app: Flask):
    app.config.setdefault("SOCK_SERVER_OPTIONS", {"max_message_size": 1024})
    sock = Sock(app)

    @sock.route("/api/v1/ws/mediciones")
    def websocket_mediciones(websocket):
        usuario_id = None
        conexion = None
        token = None
        try:
            mensaje = websocket.receive(timeout=10)
            if not isinstance(mensaje, str):
                _rechazar(websocket, "Se requiere autenticación")
                return

            try:
                autenticacion = json.loads(mensaje)
            except json.JSONDecodeError:
                _rechazar(websocket, "Mensaje de autenticación inválido")
                return

            if not isinstance(autenticacion, dict):
                _rechazar(websocket, "Mensaje de autenticación inválido")
                return
            token = autenticacion.get("token")
            if not isinstance(token, str):
                _rechazar(websocket, "Se requiere autenticación")
                return

            try:
                usuario_id = contenedor_app.servicio_tokens.validar_token(token)["sub"]
            except (ValueError, KeyError, TypeError):
                _rechazar(websocket, "La sesión no es válida")
                return

            conexion = gestor_conexiones.registrar(usuario_id, websocket)
            if not gestor_conexiones.enviar(
                conexion, json.dumps({"tipo": "autenticado"})
            ):
                return

            while True:
                mensaje = websocket.receive(timeout=20)
                if mensaje not in (None, "ping"):
                    _rechazar(websocket, "Mensaje WebSocket no reconocido")
                    return
                contenedor_app.servicio_tokens.validar_token(token)
        except ValueError:
            _rechazar(websocket, "La sesión ha expirado")
        except (ConnectionClosed, OSError):
            logger.debug("Conexión WebSocket cerrada para usuario %s", usuario_id)
        finally:
            if conexion is not None:
                gestor_conexiones.quitar(usuario_id, conexion)
