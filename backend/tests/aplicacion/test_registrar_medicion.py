from datetime import datetime

import pytest

from aplicacion.casos_uso.registrar_medicion import RegistrarMedicion
from dominio.entidades.medicion import Medicion
from dominio.entidades.planta import Planta
from dominio.excepciones.errores_dominio import (
    DispositivoNoAutorizado,
    EspecieNoEncontrada,
    ParametroAusente,
    ParametroDesconocido,
    ValorFueraDeRangoFisico,
)
from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from dominio.servicios.generador_recomendaciones import GeneradorRecomendaciones
from dominio.valores.estado_planta import EstadoPlanta
from tests.fakes import (
    HasherFake,
    RepositorioMedicionesFake,
    RepositorioPlantasFake,
    TablaReferenciaFake,
    perfil_cinta,
)

DISPOSITIVO = "ESP32_TEST_001"
TOKEN = "secreto"


def planta(especie="Cinta"):
    return Planta(id=7, usuario_id=1, especie=especie, apodo="Cinta de prueba",
                  dispositivo_id=DISPOSITIVO, token_dispositivo_hash=HasherFake().hashear(TOKEN))


def medicion(**valores):
    return Medicion(planta_id=None, fecha=datetime.now(), valores=valores)


@pytest.fixture
def repo_mediciones():
    return RepositorioMedicionesFake()


@pytest.fixture
def caso_de_uso(repo_mediciones):
    return RegistrarMedicion(
        repo_plantas=RepositorioPlantasFake([planta()]),
        hasher_tokens=HasherFake(),
        tabla_referencia=TablaReferenciaFake({"cinta": perfil_cinta()}),
        evaluador_planta=EvaluadorPlanta(EstrategiaAgregacionPorConteo(), GeneradorRecomendaciones()),
        repo_mediciones=repo_mediciones,
    )


def test_medicion_valida_se_diagnostica_y_se_guarda(caso_de_uso, repo_mediciones):
    diagnostico = caso_de_uso.ejecutar(DISPOSITIVO, TOKEN, medicion(temperatura=22, humedad=50, luz=800))

    assert diagnostico.estado_planta == EstadoPlanta.SALUDABLE
    assert len(repo_mediciones.guardadas) == 1
    assert repo_mediciones.guardadas[0].planta_id == 7


def test_medicion_anomala_pero_posible_se_guarda_como_critica(caso_de_uso, repo_mediciones):
    diagnostico = caso_de_uso.ejecutar(DISPOSITIVO, TOKEN, medicion(temperatura=40, humedad=10, luz=9000))

    assert diagnostico.estado_planta == EstadoPlanta.CRITICO
    assert len(repo_mediciones.guardadas) == 1


def test_token_incorrecto_se_rechaza_y_no_guarda(caso_de_uso, repo_mediciones):
    with pytest.raises(DispositivoNoAutorizado):
        caso_de_uso.ejecutar(DISPOSITIVO, "otro", medicion(temperatura=22, humedad=50, luz=800))
    assert repo_mediciones.guardadas == []


def test_dispositivo_inexistente_es_indistinguible_de_token_incorrecto(caso_de_uso):
    """El mensaje no debe permitir descubrir qué dispositivos existen."""
    with pytest.raises(DispositivoNoAutorizado) as por_dispositivo:
        caso_de_uso.ejecutar("NO_EXISTE", TOKEN, medicion(temperatura=22, humedad=50, luz=800))
    with pytest.raises(DispositivoNoAutorizado) as por_token:
        caso_de_uso.ejecutar(DISPOSITIVO, "otro", medicion(temperatura=22, humedad=50, luz=800))

    assert str(por_dispositivo.value) == str(por_token.value)


def test_parametro_desconocido_se_rechaza_y_no_guarda(caso_de_uso, repo_mediciones):
    with pytest.raises(ParametroDesconocido):
        caso_de_uso.ejecutar(DISPOSITIVO, TOKEN, medicion(temperatura=22, humedad=50, luz=800, ph=7))
    assert repo_mediciones.guardadas == []


def test_medicion_incompleta_se_rechaza_y_no_guarda(caso_de_uso, repo_mediciones):
    with pytest.raises(ParametroAusente):
        caso_de_uso.ejecutar(DISPOSITIVO, TOKEN, medicion(temperatura=22))
    assert repo_mediciones.guardadas == []


def test_valor_fisicamente_imposible_se_rechaza_y_no_guarda(caso_de_uso, repo_mediciones):
    with pytest.raises(ValorFueraDeRangoFisico):
        caso_de_uso.ejecutar(DISPOSITIVO, TOKEN, medicion(temperatura=9999, humedad=50, luz=800))
    assert repo_mediciones.guardadas == []


def test_especie_sin_perfil_propaga_la_excepcion_del_puerto(repo_mediciones):
    caso_de_uso = RegistrarMedicion(
        repo_plantas=RepositorioPlantasFake([planta(especie="Dinosaurio")]),
        hasher_tokens=HasherFake(),
        tabla_referencia=TablaReferenciaFake({"cinta": perfil_cinta()}),
        evaluador_planta=EvaluadorPlanta(EstrategiaAgregacionPorConteo(), GeneradorRecomendaciones()),
        repo_mediciones=repo_mediciones,
    )
    with pytest.raises(EspecieNoEncontrada):
        caso_de_uso.ejecutar(DISPOSITIVO, TOKEN, medicion(temperatura=22, humedad=50, luz=800))
    assert repo_mediciones.guardadas == []
