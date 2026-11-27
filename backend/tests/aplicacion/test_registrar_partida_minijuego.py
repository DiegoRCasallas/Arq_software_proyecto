import pytest
from datetime import date
from aplicacion.casos_uso.registrar_partida_minijuego import RegistrarPartidaMinijuego
from dominio.entidades.planta import Planta
from dominio.excepciones.errores_dominio import ErrorDominio
from dominio.servicios.motor_gamificacion import MotorGamificacion


class RepoPlantasFake:
    def __init__(self, planta):
        self.plantas = {planta.id: planta}
        self.actualizaciones = 0

    def obtener(self, planta_id: int):
        return self.plantas.get(planta_id)

    def actualizar(self, planta: Planta) -> None:
        self.plantas[planta.id] = planta
        self.actualizaciones += 1


def test_otorga_xp_y_persiste_planta():
    planta = Planta(id=1, usuario_id=7, especie="Cinta", apodo="Lola")
    repo = RepoPlantasFake(planta)
    caso_uso = RegistrarPartidaMinijuego(
        repo_plantas=repo,
        motor_gamificacion=MotorGamificacion(),
        proveedor_fecha=lambda: date(2026, 11, 23),
    )

    res = caso_uso.ejecutar(usuario_id=7, planta_id=1, puntaje=100)

    assert res["xp_ganada"] == 20
    assert res["xp_restante_hoy"] == 40
    assert res["gamificacion"]["experiencia"] == 20
    assert repo.actualizaciones == 1


def test_rechaza_usuario_que_no_es_dueno():
    planta = Planta(id=1, usuario_id=7, especie="Cinta", apodo="Lola")
    caso_uso = RegistrarPartidaMinijuego(
        repo_plantas=RepoPlantasFake(planta),
        motor_gamificacion=MotorGamificacion(),
    )

    with pytest.raises(ErrorDominio):
        caso_uso.ejecutar(usuario_id=99, planta_id=1, puntaje=50)


def test_rechaza_puntaje_invalido():
    planta = Planta(id=1, usuario_id=7, especie="Cinta", apodo="Lola")
    caso_uso = RegistrarPartidaMinijuego(
        repo_plantas=RepoPlantasFake(planta),
        motor_gamificacion=MotorGamificacion(),
    )

    with pytest.raises(ErrorDominio):
        caso_uso.ejecutar(usuario_id=7, planta_id=1, puntaje=-10)
