"""Dobles de prueba de los puertos del dominio: cumplen el mismo contrato que
los adaptadores reales (LSP) sin tocar archivos ni base de datos."""
from typing import Dict, List, Optional

from dominio.entidades.medicion import Medicion
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.entidades.planta import Planta
from dominio.excepciones.errores_dominio import EspecieNoEncontrada
from dominio.valores.rango_referencia import RangoReferencia


def perfil_cinta() -> PerfilEspecie:
    return PerfilEspecie("Cinta", {
        "temperatura": RangoReferencia("temperatura", -10, 18, 24, 50),
        "humedad": RangoReferencia("humedad", 0, 40, 60, 100),
        "luz": RangoReferencia("luz", 0, 500, 1000, 50000),
    })


class TablaReferenciaFake:
    def __init__(self, perfiles: Dict[str, PerfilEspecie]):
        self._perfiles = perfiles

    def obtener_perfil(self, especie: str) -> PerfilEspecie:
        perfil = self._perfiles.get(especie.lower())
        if perfil is None:
            raise EspecieNoEncontrada(especie)
        return perfil

    def listar_especies(self) -> List[PerfilEspecie]:
        return list(self._perfiles.values())


class RepositorioPlantasFake:
    def __init__(self, plantas: List[Planta]):
        self._plantas = plantas

    def obtener_por_dispositivo(self, dispositivo_id: str) -> Optional[Planta]:
        return next((p for p in self._plantas if p.dispositivo_id == dispositivo_id), None)

    def obtener(self, planta_id: int) -> Optional[Planta]:
        return next((p for p in self._plantas if p.id == planta_id), None)


class RepositorioMedicionesFake:
    def __init__(self):
        self.guardadas: List[Medicion] = []

    def guardar(self, medicion: Medicion) -> None:
        self.guardadas.append(medicion)

    def historial(self, planta_id: int, limite: int) -> List[Medicion]:
        return [m for m in self.guardadas if m.planta_id == planta_id][:limite]


class HasherFake:
    """'Hashea' anteponiendo 'hash:' -> determinista y sin costo de cómputo."""

    def hashear(self, texto: str) -> str:
        return f"hash:{texto}"

    def verificar(self, texto: str, hash_texto: str) -> bool:
        return hash_texto == f"hash:{texto}"
