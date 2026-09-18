"""
PerfilEspecie: agrupa los rangos de referencia de humedad, luz y temperatura
para una especie determinada.

Es lo que devuelve el puerto TablaReferencia (RA5) al consultar una especie.
"""
from dataclasses import dataclass

from dominio.valores.rango_referencia import RangoReferencia


@dataclass(frozen=True)
class PerfilEspecie:
    nombre_especie: str
    rango_humedad: RangoReferencia
    rango_luz: RangoReferencia
    rango_temperatura: RangoReferencia
