"""
Punto de entrada de la aplicación.

Este archivo pertenece a la capa de infraestructura/arranque: es el único
lugar donde se conocen Flask, CORS y el "cableado" (wiring) entre capas.
Ningún módulo de dominio ni de aplicación debería importar nada de aquí.
"""
from flask import Flask
from flask_cors import CORS

from infraestructura.config.contenedor import Contenedor
from presentacion.controladores.diagnostico_controller import crear_diagnostico_blueprint
from presentacion.controladores.especies_controller import crear_especies_blueprint


def crear_app() -> Flask:
    app = Flask(__name__)
    CORS(app)  # RA7: permite que el frontend (otro origen) consuma la API

    contenedor = Contenedor()

    app.register_blueprint(
        crear_diagnostico_blueprint(contenedor.diagnosticar_planta_use_case)
    )
    app.register_blueprint(
        crear_especies_blueprint(contenedor.listar_especies_use_case)
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    return app


if __name__ == "__main__":
    app = crear_app()
    app.run(debug=True, port=5000)
