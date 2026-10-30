from flask import Blueprint, request, jsonify
from infraestructura.config.contenedor import contenedor_app
from dominio.excepciones.errores_dominio import ErrorDominio

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/api/v1/usuarios')

@usuarios_bp.route('/registro', methods=['POST'])
def registrar():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "DATOS_INVALIDOS", "mensaje": "Se esperaba un objeto JSON"}), 400
    email = datos.get('email')
    nombre = datos.get('nombre') or (email.split('@', 1)[0] if isinstance(email, str) else None)
    contrasena = datos.get('contrasena')

    if not all([nombre, email, contrasena]):
        return jsonify({"error": "DATOS_INCOMPLETOS", "mensaje": "Nombre, email y contraseña son obligatorios"}), 400

    try:
        usuario = contenedor_app.registrar_usuario_use_case.ejecutar(nombre, email, contrasena)
        return jsonify({"mensaje": "Usuario registrado exitosamente", "usuario_id": usuario.id}), 201
    except ErrorDominio as e:
        return jsonify({"error": "ERROR_DE_NEGOCIO", "mensaje": str(e)}), 400

@usuarios_bp.route('/login', methods=['POST'])
def login():
    datos = request.get_json() or {}
    email = datos.get('email')
    contrasena = datos.get('contrasena')

    if not all([email, contrasena]):
        return jsonify({"error": "DATOS_INCOMPLETOS", "mensaje": "Email y contraseña son obligatorios"}), 400

    try:
        token = contenedor_app.iniciar_sesion_use_case.ejecutar(email, contrasena)
        return jsonify({"mensaje": "Autenticación exitosa", "token": token}), 200
    except ErrorDominio as e:
        return jsonify({"error": "NO_AUTORIZADO", "mensaje": str(e)}), 401