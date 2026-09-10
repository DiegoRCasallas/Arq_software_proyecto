"""
Puerto para la estrategia de agregación del índice de vitalidad.

Se declara en el dominio (dominio/puertos) porque EvaluadorPlanta depende
de esta abstracción, no de una implementación concreta (DIP). Cualquier
implementación que respete este contrato es sustituible sin que
EvaluadorPlanta se entere (LSP).
"""
from typing import Protocol

from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.estado_planta import EstadoPlanta


class EstrategiaAgregacion(Protocol):
    def calcular(self, estados: dict[str, EstadoParametro]) -> EstadoPlanta:
        """
        Recibe un mapeo {nombre_parametro: EstadoParametro} y devuelve
        el índice de vitalidad global.
        """
        ...
