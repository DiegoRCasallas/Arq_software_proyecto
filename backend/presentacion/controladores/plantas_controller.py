from flask import Blueprint, jsonify, request, g
from presentacion.seguridad.autenticacion import requiere_jwt
from infraestructura.config.contenedor import contenedor_app
from dominio.excepciones.errores_dominio import ErrorDominio

plantas_bp = Blueprint('plantas', __name__, url_prefix='/api/v1/plantas')


def _serializar_planta(planta, historial=None):
    ultima_medicion = None
    if historial:
        item = historial[0]
        medicion = item["medicion"]
        diagnostico = item["diagnostico"]
        ultima_medicion = {
            "fecha": medicion.fecha.isoformat(),
            "valores": medicion.valores,
            "detalle_parametros": {
                parametro: estado.name for parametro, estado in diagnostico.estados.items()
            },
            "estado_general": diagnostico.estado_planta.name,
            "recomendaciones": diagnostico.recomendaciones,
        }

    return {
        "id": planta.id,
        "apodo": planta.apodo,
        "especie": planta.especie,
        "dispositivo_conectado": bool(planta.dispositivo_id),
        "ultima_medicion": ultima_medicion,
    }


def _historial(planta_id, limite):
    return contenedor_app.consultar_historial_use_case.ejecutar(
        g.usuario_id, planta_id, limite
    )


@plantas_bp.route('', methods=['GET'])
@requiere_jwt
def listar_plantas():
    try:
        plantas = contenedor_app.repo_plantas.listar_por_usuario(g.usuario_id)
        respuesta = [
            _serializar_planta(planta, _historial(planta.id, 1))
            for planta in plantas
        ]
        return jsonify(respuesta), 200
    except ErrorDominio as e:
        return jsonify({"error": "ERROR_DE_NEGOCIO", "mensaje": str(e)}), 400


@plantas_bp.route('', methods=['POST'])
@requiere_jwt
def crear_planta():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "DATOS_INVALIDOS", "mensaje": "Se esperaba un objeto JSON"}), 400

    especie = datos.get("especie")
    apodo = datos.get("apodo")
    if not isinstance(especie, str) or not especie.strip():
        return jsonify({"error": "DATOS_INCOMPLETOS", "mensaje": "La especie es obligatoria"}), 400
    if apodo is not None and (not isinstance(apodo, str) or len(apodo.strip()) > 60):
        return jsonify({"error": "DATOS_INVALIDOS", "mensaje": "El nombre debe tener hasta 60 caracteres"}), 400

    try:
        contenedor_app.tabla_referencia.obtener_perfil(especie.strip())
        from dominio.entidades.planta import Planta

        planta = Planta(
            id=None,
            usuario_id=g.usuario_id,
            especie=especie.strip(),
            apodo=apodo.strip() or None if apodo else None,
        )
        planta = contenedor_app.repo_plantas.guardar(planta)
        return jsonify(_serializar_planta(planta)), 201
    except ErrorDominio as e:
        return jsonify({"error": "ERROR_DE_NEGOCIO", "mensaje": str(e)}), 400


@plantas_bp.route('/<int:planta_id>', methods=['GET'])
@requiere_jwt
def obtener_planta(planta_id):
    planta = contenedor_app.repo_plantas.obtener(planta_id)
    if planta is None or not planta.pertenece_a(g.usuario_id):
        return jsonify({"error": "PLANTA_NO_ENCONTRADA", "mensaje": "La planta no existe"}), 404

    try:
        return jsonify(_serializar_planta(planta, _historial(planta_id, 1))), 200
    except ErrorDominio as e:
        return jsonify({"error": "ERROR_DE_NEGOCIO", "mensaje": str(e)}), 400


@plantas_bp.route('/<int:planta_id>', methods=['DELETE'])
@requiere_jwt
def eliminar_planta(planta_id):
    planta = contenedor_app.repo_plantas.obtener(planta_id)
    if planta is None or not planta.pertenece_a(g.usuario_id):
        return jsonify({"error": "PLANTA_NO_ENCONTRADA", "mensaje": "La planta no existe"}), 404

    contenedor_app.repo_plantas.eliminar(planta_id)
    return jsonify({"mensaje": "Planta eliminada"}), 200


@plantas_bp.route('/<int:planta_id>/historial', methods=['GET'])
@requiere_jwt
def historial(planta_id):
    limite = request.args.get('limite', default=10, type=int)
    usuario_id = g.usuario_id

    try:
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
    except Exception:
        return jsonify({"error": "ERROR_INTERNO", "mensaje": "Fallo al consultar el historial"}), 500