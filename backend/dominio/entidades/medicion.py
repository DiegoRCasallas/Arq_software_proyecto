"""
Medicion: conjunto de valores que un dispositivo (ESP32) midió en un
instante para una planta.

Los valores son dinámicos ({nombre_parametro: valor}): el dominio no asume
que existan solo temperatura, humedad y luz. Qué parámetros son válidos lo
decide el PerfilEspecie de la planta (ver PerfilEspecie.validar_medicion).

RA6: el dominio nunca recibe un dict crudo ni un request; la conversión y
validación de tipos ocurre en el borde (presentacion/dto).
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Medicion:
    planta_id: Optional[int]
    fecha: datetime
    valores: Dict[str, float]
