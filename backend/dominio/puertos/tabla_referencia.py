"""
Puerto TablaReferencia (RA5): abstracción que el dominio declara para
consultar perfiles de especies, sin conocer si detrás hay un CSV, una
base de datos o cualquier otra fuente.

ISP: solo expone las dos operaciones que el dominio realmente necesita,
no una interfaz de repositorio genérica con operaciones de escritura,
paginación, etc. que nadie en el dominio usa.

La dirección de la dependencia es infraestructura -> dominio: una clase
concreta en infraestructura (p. ej. TablaReferenciaCSV) implementará este
Protocol. El dominio (EvaluadorPlanta, casos de uso) solo conoce esta
interfaz.
"""
from typing import Protocol

from dominio.entidades.perfil_especie import PerfilEspecie


class TablaReferencia(Protocol):
    def obtener_perfil(self, especie: str) -> PerfilEspecie:
        """
        Devuelve el PerfilEspecie de la especie dada.
        Lanza EspecieNoEncontrada si la especie no existe.
        """
        ...

    def listar_especies(self) -> list[PerfilEspecie]:
        """Devuelve los perfiles de todas las especies soportadas (RF5)."""
        ...
