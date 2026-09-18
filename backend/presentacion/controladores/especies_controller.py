"""
Controlador de especies: expone RF5 (consultar especies soportadas y
sus rangos de referencia).
"""
from flask import Blueprint, jsonify

from aplicacion.casos_uso.listar_especies import ListarEspeciesUseCase
from presentacion.dto.serializadores import serializar_perfil_especie


def crear_especies_blueprint(caso_de_uso: ListarEspeciesUseCase) -> Blueprint:
    blueprint = Blueprint("especies", __name__)

    @blueprint.get("/especies")
    def listar_especies():
        perfiles = caso_de_uso.ejecutar()
        return jsonify([serializar_perfil_especie(p) for p in perfiles]), 200

    return blueprint
