"""
Estado global de la planta (RF3), resultado de agregar los estados
individuales de humedad, luz y temperatura.

Se usa el nombre "índice de vitalidad" de forma consistente en todo
el dominio y en el documento de arquitectura.
"""
from enum import Enum


class EstadoPlanta(str, Enum):
    SALUDABLE = "SALUDABLE"
    EN_RIESGO = "EN_RIESGO"
    CRITICO = "CRITICO"
