import pytest
from aplicacion.casos_uso.vincular_dispositivo import VincularDispositivo
from dominio.entidades.planta import Planta
from dominio.excepciones.errores_dominio import ErrorDominio


class HasherFake:
    def hashear(self, texto: str) -> str:
        return f"hash:{texto}"


class RepoPlantasFake:
    def __init__(self, plantas):
        self.plantas = {p.id: p for p in plantas}

    def obtener(self, planta_id: int):
        return self.plantas.get(planta_id)

    def obtener_por_dispositivo(self, dispositivo_id: str):
        for p in self.plantas.values():
            if p.dispositivo_id == dispositivo_id:
                return p
        return None

    def actualizar_dispositivo(self, planta_id: int, dispositivo_id, token_hash):
        p = self.plantas[planta_id]
        p.dispositivo_id = dispositivo_id
        p.token_dispositivo_hash = token_hash


def test_mismo_usuario_puede_mover_dispositivo_entre_sus_plantas():
    p1 = Planta(id=1, usuario_id=10, especie="Cinta", apodo="Uno", dispositivo_id="ESP1", token_dispositivo_hash="hash:abc")
    p2 = Planta(id=2, usuario_id=10, especie="Poto", apodo="Dos")
    repo = RepoPlantasFake([p1, p2])
    caso_uso = VincularDispositivo(repo, HasherFake())

    res = caso_uso.ejecutar(usuario_id=10, planta_id=2, dispositivo_id="ESP1", token_plano="abc")

    assert p1.dispositivo_id is None
    assert p2.dispositivo_id == "ESP1"
    assert res["reasignado_desde_planta_id"] == 1


def test_otro_usuario_no_puede_robar_dispositivo():
    p1 = Planta(id=1, usuario_id=10, especie="Cinta", apodo="Uno", dispositivo_id="ESP1", token_dispositivo_hash="hash:abc")
    p2 = Planta(id=2, usuario_id=99, especie="Poto", apodo="Ajena")
    repo = RepoPlantasFake([p1, p2])
    caso_uso = VincularDispositivo(repo, HasherFake())

    with pytest.raises(ErrorDominio):
        caso_uso.ejecutar(usuario_id=99, planta_id=2, dispositivo_id="ESP1", token_plano="abc")
