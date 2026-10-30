from flask import Blueprint, jsonify, request, g
from presentacion.seguridad.autenticacion import requiere_jwt
from infraestructura.config.contenedor import contenedor_app
from dominio.excepciones.errores_dominio import ErrorDominio

plantas_bp = Blueprint('plantas', __name__, url_prefix='/api/v1/plantas')

@plantas_bp.route('/<int:planta_id>/historial', methods=['GET'])
@requiere_jwt
def historial(planta_id):
    # Permite al frontend enviar un límite personalizado por URL, ej: ?limite=20
    limite = request.args.get('limite', default=10, type=int)
    usuario_id = g.usuario_id

    try:
        mediciones = contenedor_app.consultar_historial_use_case.ejecutar(usuario_id, planta_id, limite)
        
        # Transformamos las entidades puras a JSON para el frontend
        resultado = []
        for m in mediciones:
            resultado.append({
                "fecha": m.fecha.isoformat(),
                "valores": m.valores
            })
            
        return jsonify(resultado), 200

    except ErrorDominio as e:
        return jsonify({"error": "ERROR_DE_NEGOCIO", "mensaje": str(e)}), 400
    except Exception as e:
        print(f"Error consultando historial: {e}")
        return jsonify({"error": "ERROR_INTERNO", "mensaje": "Fallo al consultar el historial"}), 500