from typing import Protocol, List, Optional
from dominio.entidades.planta import Planta

class RepositorioPlantas(Protocol):
    def obtener(self, planta_id: int) -> Optional[Planta]:
        ...
        
    def obtener_por_dispositivo(self, dispositivo_id: str) -> Optional[Planta]:
        ...
        
    def listar_por_usuario(self, usuario_id: int) -> List[Planta]:
        ...
        
    def guardar(self, planta: Planta) -> Planta:
        ...