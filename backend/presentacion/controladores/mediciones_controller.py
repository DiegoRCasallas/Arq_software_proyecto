import logging
import re

from flask import Blueprint, request, jsonify

from dominio.excepciones.errores_dominio import ErrorDominio
from infraestructura.config.contenedor import contenedor_app
from presentacion.dto.manejador_errores import manejar_error_dominio
from presentacion.dto.serializadores import serializar_diagnostico
from presentacion.dto.validadores_request import construir_medicion
from presentacion.ws.mediciones import emitir_medicion

logger = logging.getLogger(__name__)

# Definimos el blueprint para agrupar las rutas de los dispositivos
dispositivos_bp = Blueprint('dispositivos', __name__, url_prefix='/api/v1/dispositivos')

@dispositivos_bp.route('/<dispositivo_id>/vinculacion/preparar', methods=['POST'])
def preparar_vinculacion_endpoint(dispositivo_id):
    codigo = request.headers.get('X-Pairing-Code', '')
    token_dispositivo = request.headers.get('X-Device-Token', '')
    if (
        not re.fullmatch(r"[a-fA-F0-9]{24}", dispositivo_id)
        or not re.fullmatch(r"[a-fA-F0-9]{32}", codigo)
        or not re.fullmatch(r"[a-fA-F0-9]{64}", token_dispositivo)
    ):
        return jsonify({"error": "DATOS_INVALIDOS", "mensaje": "Credenciales de vinculacion invalidas"}), 400

    try:
        resultado = contenedor_app.vinculacion_qr_use_case.preparar(
            dispositivo_id=dispositivo_id.lower(),
            codigo=codigo.lower(),
            token_dispositivo=token_dispositivo.lower(),
        )
        return jsonify(resultado), 200
    except ErrorDominio as e:
        mensaje = str(e)
        status = 410 if "inválido o expirado" in mensaje.lower() else 409
        return jsonify({"error": "VINCULACION_NO_PREPARADA", "mensaje": mensaje}), status


@dispositivos_bp.route('/<dispositivo_id>/vinculacion/confirmar', methods=['POST'])
def confirmar_vinculacion_endpoint(dispositivo_id):
    codigo = request.headers.get('X-Pairing-Code', '')
    token_dispositivo = request.headers.get('X-Device-Token', '')
    if (
        not re.fullmatch(r"[a-fA-F0-9]{24}", dispositivo_id)
        or not re.fullmatch(r"[a-fA-F0-9]{32}", codigo)
        or not re.fullmatch(r"[a-fA-F0-9]{64}", token_dispositivo)
    ):
        return jsonify({"error": "DATOS_INVALIDOS", "mensaje": "Credenciales de vinculación inválidas"}), 400

    try:
        resultado = contenedor_app.vinculacion_qr_use_case.confirmar(
            dispositivo_id=dispositivo_id.lower(),
            codigo=codigo.lower(),
            token_dispositivo=token_dispositivo.lower(),
            aprobar=request.headers.get("X-Pairing-Approval") == "confirm",
        )
        esperando = resultado["estado"] in {"esperando", "solicitada"}
        return jsonify(resultado), 202 if esperando else 200
    except ErrorDominio as e:
        mensaje = str(e)
        if "credencial de dispositivo" in mensaje.lower():
            status = 401
        elif "inválido o expirado" in mensaje.lower():
            status = 410
        else:
            status = 409
        return jsonify({"error": "VINCULACION_NO_COMPLETADA", "mensaje": mensaje}), status


@dispositivos_bp.route('/<dispositivo_id>/mediciones', methods=['POST'])
def registrar_medicion_endpoint(dispositivo_id):
    """
    Endpoint consumido por el ESP32 (o el simulador) para enviar lecturas.

    Respuestas:
      201 medición aceptada y guardada (cuerpo: diagnóstico)
      400 medición rechazada (formato, valor no numérico, parámetro desconocido
          o ausente, valor físicamente imposible); NO se guarda nada
      401 falta el token, o dispositivo/token inválido
      500 error inesperado del servidor
    """
    # 1. Token propio del dispositivo (R7)
    token_dispositivo = request.headers.get('X-Device-Token')
    if not token_dispositivo:
        return jsonify({"error": "AUTORIZACION_DENEGADA", "mensaje": "Falta X-Device-Token"}), 401

    try:
        # 2. HTTP/JSON -> objeto puro del dominio. silent=True: un cuerpo que no
        #    sea JSON da None (y un 400 JSON uniforme), no una página HTML de Flask.
        medicion = construir_medicion(request.get_json(silent=True))

        # 3. Entregar el control a la aplicación/dominio
        diagnostico = contenedor_app.registrar_medicion_use_case.ejecutar(
            dispositivo_id, token_dispositivo, medicion
        )

        # 4. Notificar en vivo después de persistir la medición.
        planta = contenedor_app.repo_plantas.obtener_por_dispositivo(dispositivo_id)
        if planta is not None:
            emitir_medicion(planta.usuario_id, {
                "tipo": "medicion",
                "planta_id": planta.id,
                "medicion": {
                    "fecha": medicion.fecha.isoformat(),
                    "valores": medicion.valores,
                    **serializar_diagnostico(diagnostico),
                },
            })

        # 5. Dominio -> JSON
        return jsonify(serializar_diagnostico(diagnostico)), 201

    except ErrorDominio as e:
        cuerpo, status_http = manejar_error_dominio(e)
        return jsonify(cuerpo), status_http
    except Exception:
        logger.exception("Error inesperado registrando medición del dispositivo %s", dispositivo_id)
        return jsonify({"error": "ERROR_INTERNO", "mensaje": "Fallo procesando la medición"}), 500
