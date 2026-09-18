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
from dataclasses import dataclass


@dataclass(frozen=True)
class LecturaSensor:
    humedad: float
    luz: float
    temperatura: float
