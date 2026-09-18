"""
Controlador de diagnóstico: único punto donde Flask, JSON crudo y HTTP
se tocan con el resto del sistema.

Responsabilidad (SRP): recibir la petición, convertirla a objetos de
dominio (vía presentacion/dto), invocar el caso de uso, y traducir el
resultado (o el error) a una respuesta HTTP. No contiene reglas de
negocio.
"""
from flask import Blueprint, request, jsonify

from aplicacion.casos_uso.diagnosticar_planta import DiagnosticarPlantaUseCase
from presentacion.dto.lectura_request import construir_lectura_desde_json
from presentacion.dto.serializadores import serializar_diagnostico
from presentacion.dto.manejador_errores import manejar_error_dominio
from dominio.excepciones.errores_dominio import ErrorDominio


def crear_diagnostico_blueprint(caso_de_uso: DiagnosticarPlantaUseCase) -> Blueprint:
    blueprint = Blueprint("diagnostico", __name__)

    @blueprint.post("/diagnostico")
    def diagnosticar():
        cuerpo = request.get_json(silent=True)
        try:
            especie, lectura = construir_lectura_desde_json(cuerpo)
            diagnostico = caso_de_uso.ejecutar(especie, lectura)
            return jsonify(serializar_diagnostico(diagnostico)), 200
        except ErrorDominio as error:
            cuerpo_error, status_http = manejar_error_dominio(error)
            return jsonify(cuerpo_error), status_http

    return blueprint
