from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SesionVinculacion:
    id: str
    dispositivo_id: str
    usuario_id: Optional[int]
    planta_id: Optional[int]
    codigo_hash: str
    token_dispositivo_hash: str
    expira_en: datetime
    completada_en: Optional[datetime] = None

