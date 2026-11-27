from datetime import datetime
from typing import Optional, Protocol

from dominio.entidades.sesion_vinculacion import SesionVinculacion


class RepositorioSesionesVinculacion(Protocol):
    def crear(self, sesion: SesionVinculacion) -> None:
        ...

    def obtener_por_dispositivo(
        self, dispositivo_id: str
    ) -> Optional[SesionVinculacion]:
        ...

    def obtener(self, sesion_id: str) -> Optional[SesionVinculacion]:
        ...

    def obtener_por_codigo(
        self, dispositivo_id: str, codigo_hash: str
    ) -> Optional[SesionVinculacion]:
        ...

    def reclamar(
        self, sesion_id: str, usuario_id: int, planta_id: int
    ) -> bool:
        ...

    def marcar_completada(self, sesion_id: str, fecha: datetime) -> None:
        ...

    def cancelar(self, sesion_id: str, fecha: datetime) -> None:
        ...

