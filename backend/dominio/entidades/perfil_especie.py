"""
PerfilEspecie: agrupa los rangos de referencia de humedad, luz y temperatura
para una especie determinada.
"""
from typing import Dict
from dominio.valores.rango_referencia import RangoReferencia

class PerfilEspecie:
    def __init__(self, nombre_especie: str, rangos: Dict[str, RangoReferencia]):
        self.nombre_especie = nombre_especie
        self.rangos = rangos