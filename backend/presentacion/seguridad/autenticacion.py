from functools import wraps
from flask import request, jsonify, g
from infraestructura.config.contenedor import contenedor_app

def requiere_jwt(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        token = None
        
        # 1. Buscar el token en el encabezado Authorization
        if 'Authorization' in request.headers:
            partes = request.headers['Authorization'].split()
            if len(partes) == 2 and partes[0] == 'Bearer':
                token = partes[1]

        if not token:
            return jsonify({"error": "NO_AUTORIZADO", "mensaje": "Falta el token de autorización (Bearer)"}), 401

        try:
            # 2. Validar el token delegando la responsabilidad a nuestro adaptador configurado en el contenedor
            payload = contenedor_app.servicio_tokens.validar_token(token)
            
            # 3. Inyectar el ID del usuario en el contexto de Flask
            g.usuario_id = payload['sub']
            
        except ValueError as e:
            return jsonify({"error": "TOKEN_INVALIDO", "mensaje": str(e)}), 401
        except Exception:
            return jsonify({"error": "ERROR_SERVIDOR", "mensaje": "Fallo al procesar el token"}), 500

        return f(*args, **kwargs)
    return decorador