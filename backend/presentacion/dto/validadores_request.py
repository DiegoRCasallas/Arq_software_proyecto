"""
Validación y transformación del cuerpo HTTP de una medición hacia objetos
del dominio (RA6).

Esta es la frontera del sistema: aquí, y solo aquí, se acepta un dict crudo
(el JSON deserializado). Se encarga de la validación de FORMA y TIPO:
que haya un objeto "valores" y que cada valor sea un número finito. Las
reglas de negocio (parámetros válidos, rango físico) viven en el dominio.
"""
import math
from datetime import datetime

from dominio.entidades.medicion import Medicion
from dominio.excepciones.errores_dominio import ParametroAusente, ValorNoNumerico


def _a_numero(nombre_parametro: str, valor) -> float:
    """
    Convierte a float rechazando todo lo que no sea una lectura numérica real.

    Casos típicos de un sensor defectuoso o un firmware con errores:
      - null / None        (sensor desconectado)
      - NaN / Infinity     (float("nan") "convierte" bien pero es inservible)
      - true / false       (bool es subclase de int en Python: float(True) == 1.0)
      - listas, objetos, texto no numérico
    """
    if valor is None or isinstance(valor, bool):
        raise ValorNoNumerico(nombre_parametro, valor)
    try:
        numero = float(valor)
    except (TypeError, ValueError, OverflowError):
        raise ValorNoNumerico(nombre_parametro, valor)
    if not math.isfinite(numero):
        raise ValorNoNumerico(nombre_parametro, valor)
    return numero


def construir_medicion(json_data) -> Medicion:
    valores = json_data.get("valores") if isinstance(json_data, dict) else None

    if not isinstance(valores, dict) or not valores:
        raise ParametroAusente("valores")

    valores_limpios = {nombre: _a_numero(nombre, valor) for nombre, valor in valores.items()}

    # planta_id se asigna después de autenticar al dispositivo, en el caso de uso.
    return Medicion(planta_id=None, fecha=datetime.now(), valores=valores_limpios)
