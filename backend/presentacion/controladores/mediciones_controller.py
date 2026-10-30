import logging

from flask import Blueprint, request, jsonify

from dominio.excepciones.errores_dominio import ErrorDominio
from infraestructura.config.contenedor import contenedor_app
from presentacion.dto.manejador_errores import manejar_error_dominio
from presentacion.dto.serializadores import serializar_diagnostico
from presentacion.dto.validadores_request import construir_medicion

logger = logging.getLogger(__name__)

# Definimos el blueprint para agrupar las rutas de los dispositivos
dispositivos_bp = Blueprint('dispositivos', __name__, url_prefix='/api/v1/dispositivos')


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

        # 4. Dominio -> JSON
        return jsonify(serializar_diagnostico(diagnostico)), 201

    except ErrorDominio as e:
        cuerpo, status_http = manejar_error_dominio(e)
        return jsonify(cuerpo), status_http
    except Exception:
        logger.exception("Error inesperado registrando medición del dispositivo %s", dispositivo_id)
        return jsonify({"error": "ERROR_INTERNO", "mensaje": "Fallo procesando la medición"}), 500
