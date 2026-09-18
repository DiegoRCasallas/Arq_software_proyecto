"""
Serializadores: convierten entidades del dominio a diccionarios listos
para json.jsonify(). Viven en presentación porque el formato de salida
(nombres de campos JSON, estructura) es una decisión de la API, no del
dominio -- el dominio no debería tener que cambiar si mañana se decide
renombrar un campo en la respuesta HTTP.
"""
from dominio.entidades.diagnostico_planta import DiagnosticoPlanta
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.valores.rango_referencia import RangoReferencia


def serializar_diagnostico(diagnostico: DiagnosticoPlanta) -> dict:
    return {
        "estados": {
            "humedad": diagnostico.estado_humedad.value,
            "luz": diagnostico.estado_luz.value,
            "temperatura": diagnostico.estado_temperatura.value,
        },
        "indice_vitalidad": diagnostico.indice_vitalidad.value,
        "recomendaciones": diagnostico.recomendaciones,
    }


def _serializar_rango(rango: RangoReferencia) -> dict:
    return {
        "minimo": rango.minimo,
        "optimo_min": rango.optimo_min,
        "optimo_max": rango.optimo_max,
        "maximo": rango.maximo,
    }


def serializar_perfil_especie(perfil: PerfilEspecie) -> dict:
    return {
        "especie": perfil.nombre_especie,
        "rangos": {
            "humedad": _serializar_rango(perfil.rango_humedad),
            "luz": _serializar_rango(perfil.rango_luz),
            "temperatura": _serializar_rango(perfil.rango_temperatura),
        },
    }
