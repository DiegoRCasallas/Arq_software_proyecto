from flask import Blueprint, request, jsonify
from dominio.excepciones.errores_dominio import ErrorDominio
from presentacion.dto.validadores_request import construir_medicion
from presentacion.dto.serializadores import serializar_diagnostico

# Definimos el blueprint para agrupar las rutas de los dispositivos
dispositivos_bp = Blueprint('dispositivos', __name__, url_prefix='/api/v1/dispositivos')

@dispositivos_bp.route('/<dispositivo_id>/mediciones', methods=['POST'])
def registrar_medicion_endpoint(dispositivo_id):
    """
    Endpoint consumido por el simulador ESP32 para enviar lecturas.
    """
    # 1. Extraer el token de autenticación propio del dispositivo (R7)
    token_dispositivo = request.headers.get('X-Device-Token')
    if not token_dispositivo:
        return jsonify({"error": "AUTORIZACION_DENEGADA", "mensaje": "Falta X-Device-Token"}), 401
        
    # 2. Extraer el payload
    datos_json = request.get_json()
    if not datos_json or 'valores' not in datos_json:
        return jsonify({"error": "FORMATO_INVALIDO", "mensaje": "El JSON debe incluir 'valores'"}), 400
        
    try:
        # 3. Transformar de HTTP/JSON a objetos puros del dominio
        medicion = construir_medicion(datos_json)
        
        # 4. Obtener el caso de uso instanciado desde el contenedor de composición (RUTA CORREGIDA)
        from infraestructura.config.contenedor import registrar_medicion_use_case
        
        # 5. Entregar el control al dominio
        diagnostico = registrar_medicion_use_case.ejecutar(dispositivo_id, token_dispositivo, medicion)
        
        # 6. Transformar la respuesta
        respuesta = serializar_diagnostico(diagnostico)
        
        return jsonify(respuesta), 201
        
    except ErrorDominio as e:
        return jsonify({"error": "ERROR_DE_NEGOCIO", "mensaje": str(e)}), 400
    except Exception as e:
        # Imprimimos el error real en la consola de Flask para poder depurar
        print(f"CRASH INTERNO: {e}") 
        return jsonify({"error": "ERROR_INTERNO", "mensaje": "Fallo procesando la medición"}), 500