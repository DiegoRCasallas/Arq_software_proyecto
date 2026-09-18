"""
Punto de entrada de la aplicación.

Este archivo pertenece a la capa de infraestructura/arranque: es el único
lugar donde se conocen Flask, CORS y el "cableado" (wiring) entre capas.
Ningún módulo de dominio ni de aplicación debería importar nada de aquí.
"""
from flask import Flask
from flask_cors import CORS


def crear_app() -> Flask:
    app = Flask(__name__)
    CORS(app)  # RA7: permite que el frontend (otro origen) consuma la API

    # Aquí se registrarán los blueprints/controladores de la capa de
    # presentación a medida que se vayan construyendo, por ejemplo:
    # from presentacion.controladores.diagnostico_controller import diagnostico_bp
    # app.register_blueprint(diagnostico_bp)

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app


if __name__ == "__main__":
    app = crear_app()
    app.run(debug=True, port=5000)
