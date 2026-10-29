"""
Punto de entrada de la aplicación.

Este archivo pertenece a la capa de infraestructura/arranque: es el único
lugar donde se conocen Flask, CORS y el "cableado" (wiring) entre capas.
Ningún módulo de dominio ni de aplicación debería importar nada de aquí.
"""
from flask import Flask, jsonify
from presentacion.controladores.mediciones_controller import dispositivos_bp

def create_app():
    app = Flask(__name__)

    # Registrar las rutas (Blueprints)
    app.register_blueprint(dispositivos_bp)

    # Manejador global para rutas no encontradas
    @app.errorhandler(404)
    def no_encontrado(e):
        return jsonify({"error": "RUTA_NO_ENCONTRADA", "mensaje": "El endpoint solicitado no existe"}), 404

    return app

if __name__ == '__main__':
    app = create_app()
    # Ejecutamos el servidor en el puerto 5000
    app.run(debug=True, host='0.0.0.0', port=5000)