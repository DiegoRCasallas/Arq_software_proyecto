"""
Estados posibles para un parámetro individual (humedad, luz, temperatura)
tras compararlo contra su rango de referencia.

Pertenece al dominio puro: no depende de nada externo.
"""
from enum import Enum


class EstadoParametro(str, Enum):
    BAJO = "BAJO"
    OPTIMO = "OPTIMO"
    ALTO = "ALTO"
