"""
Estado global de la planta (RF3), resultado de agregar los estados
individuales de todos sus parámetros.

INDETERMINADO significa "no hubo ningún parámetro evaluable": no se puede
afirmar que la planta esté bien ni mal. Es preferible a devolver SALUDABLE
por falta de datos (un diagnóstico optimista sin evidencia es peligroso).

Se usa el nombre "índice de vitalidad" de forma consistente en todo
el dominio y en el documento de arquitectura.
"""
from enum import Enum


class EstadoPlanta(str, Enum):
    SALUDABLE = "SALUDABLE"
    EN_RIESGO = "EN_RIESGO"
    CRITICO = "CRITICO"
    INDETERMINADO = "INDETERMINADO"
