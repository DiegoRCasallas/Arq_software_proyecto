"""
LecturaSensor: representa una medición de humedad, luz y temperatura ya
validada y convertida a tipos numéricos (RA6 — el dominio nunca recibe
un dict crudo ni un request; eso se resuelve en el borde del sistema,
en la capa de aplicación/presentación).

Nota de diseño: esta clase NO incluye la especie. La especie se usa para
buscar el PerfilEspecie correspondiente (vía el puerto TablaReferencia),
pero la lectura en sí es independiente de la especie: los mismos tres
números podrían evaluarse contra perfiles distintos. Mantenerlos separados
respeta SRP: LecturaSensor solo representa "lo que midió el sensor".
"""
from datetime import datetime
from typing import Dict, Optional

class Medicion:
    def __init__(self, planta_id: Optional[int], fecha: datetime, valores: Dict[str, float]):
        self.planta_id = planta_id
        self.fecha = fecha
        self.valores = valores