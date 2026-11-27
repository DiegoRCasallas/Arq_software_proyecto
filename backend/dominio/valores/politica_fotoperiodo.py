from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PoliticaFotoperiodo:
    hora_inicio_noche: int = 18        # 6:00 PM
    hora_fin_noche: int = 6            # 6:00 AM
    horas_oscuridad_maximas: float = 14.0

    def es_horario_nocturno(self, fecha: datetime) -> bool:
        hora = fecha.hour
        if self.hora_inicio_noche > self.hora_fin_noche:
            # Cruza medianoche (ej. 18:00 a 06:00)
            return hora >= self.hora_inicio_noche or hora < self.hora_fin_noche
        return self.hora_inicio_noche <= hora < self.hora_fin_noche
