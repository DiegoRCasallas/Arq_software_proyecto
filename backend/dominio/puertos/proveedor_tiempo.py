from datetime import datetime
from typing import Protocol


class ProveedorTiempo(Protocol):
    def ahora(self) -> datetime:
        ...
