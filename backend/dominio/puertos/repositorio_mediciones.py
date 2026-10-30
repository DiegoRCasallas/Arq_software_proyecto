from typing import Protocol, List
from dominio.entidades.medicion import Medicion

class RepositorioMediciones(Protocol):
    def guardar(self, medicion: Medicion) -> None:
        ...
        
    def historial(self, planta_id: int, limite: int) -> List[Medicion]:
        ...