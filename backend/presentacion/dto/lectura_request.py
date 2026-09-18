"""
Validación y transformación de la petición HTTP de diagnóstico hacia
objetos del dominio (RA6).

Esta es la frontera del sistema: aquí, y solo aquí, se acepta un dict
crudo (el JSON deserializado de la petición). Todo lo que cruce hacia
aplicación/dominio ya debe ser un tipo del dominio (LecturaSensor) o un
str simple (especie).

Las excepciones de dominio (ParametroAusente, ValorNoNumerico) se lanzan
aquí mismo, para que el controlador las traduzca a códigos HTTP (RF6).
"""
from dominio.entidades.lectura_sensor import LecturaSensor
from dominio.excepciones.errores_dominio import ParametroAusente, ValorNoNumerico

_CAMPOS_REQUERIDOS = ("especie", "humedad", "temperatura", "luz")


def _a_numero(nombre_parametro: str, valor) -> float:
    if isinstance(valor, bool):  # bool es subclase de int en Python; se excluye explícitamente
        raise ValorNoNumerico(nombre_parametro, valor)
    try:
        return float(valor)
    except (TypeError, ValueError):
        raise ValorNoNumerico(nombre_parametro, valor)


def construir_lectura_desde_json(cuerpo: dict) -> tuple[str, LecturaSensor]:
    """
    Valida el cuerpo crudo de la petición POST /diagnostico y lo convierte
    en (especie, LecturaSensor). Lanza ParametroAusente o ValorNoNumerico
    si algo no es válido.
    """
    if not isinstance(cuerpo, dict):
        raise ParametroAusente("cuerpo de la petición")

    for campo in _CAMPOS_REQUERIDOS:
        if campo not in cuerpo or cuerpo[campo] is None:
            raise ParametroAusente(campo)

    especie = str(cuerpo["especie"]).strip()
    if not especie:
        raise ParametroAusente("especie")

    humedad = _a_numero("humedad", cuerpo["humedad"])
    temperatura = _a_numero("temperatura", cuerpo["temperatura"])
    luz = _a_numero("luz", cuerpo["luz"])

    lectura = LecturaSensor(humedad=humedad, luz=luz, temperatura=temperatura)
    return especie, lectura
