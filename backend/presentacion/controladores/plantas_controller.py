from flask import Blueprint, jsonify, request, g
from presentacion.seguridad.autenticacion import requiere_jwt
from infraestructura.config.contenedor import contenedor_app
from dominio.excepciones.errores_dominio import ErrorDominio

plantas_bp = Blueprint('plantas', __name__, url_prefix='/api/v1/plantas')

@plantas_bp.route('/<int:planta_id>/historial', methods=['GET'])
@requiere_jwt
def historial(planta_id):
    limite = request.args.get('limite', default=10, type=int)
    usuario_id = g.usuario_id

    try:
        # El caso de uso devuelve una lista de diccionarios con la entidad Medicion y la entidad DiagnosticoPlanta
        resultados = contenedor_app.consultar_historial_use_case.ejecutar(usuario_id, planta_id, limite)
        
        respuesta = []
        for item in resultados:
            m = item["medicion"]
            d = item["diagnostico"]
            
            respuesta.append({
                "fecha": m.fecha.isoformat(),
                "valores": m.valores,
                "detalle_parametros": {param: estado.name for param, estado in d.estados.items()},
                "estado_general": d.estado_planta.name,
                "recomendaciones": d.recomendaciones
            })
            
        return jsonify(respuesta), 200

    except ErrorDominio as e:
        return jsonify({"error": "ERROR_DE_NEGOCIO", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"Error consultando historial: {e}")
        return jsonify({"error": "ERROR_INTERNO", "mensaje": "Fallo al consultar el historial"}), 500