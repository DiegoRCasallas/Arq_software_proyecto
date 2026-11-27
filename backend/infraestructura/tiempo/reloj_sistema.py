from datetime import datetime
from zoneinfo import ZoneInfo


class RelojSistema:
    def __init__(self, zona_horaria: str = "America/Bogota"):
        self._tz = ZoneInfo(zona_horaria)

    def ahora(self) -> datetime:
        # Retorna hora local de Colombia sin tzinfo para compatibilidad directa con SQLite
        return datetime.now(self._tz).replace(tzinfo=None)
