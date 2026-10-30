from datetime import datetime

import pytest

from dominio.entidades.medicion import Medicion
from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from dominio.servicios.generador_recomendaciones import GeneradorRecomendaciones
from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.estado_planta import EstadoPlanta
from tests.fakes import perfil_cinta


@pytest.fixture
def evaluador():
    return EvaluadorPlanta(EstrategiaAgregacionPorConteo(), GeneradorRecomendaciones())


def medicion(**valores):
    return Medicion(planta_id=1, fecha=datetime.now(), valores=valores)


def test_planta_saludable_cuando_todo_esta_en_optimo(evaluador):
    d = evaluador.evaluar(medicion(temperatura=22, humedad=50, luz=800), perfil_cinta())

    assert d.estados == {
        "temperatura": EstadoParametro.OPTIMO,
        "humedad": EstadoParametro.OPTIMO,
        "luz": EstadoParametro.OPTIMO,
    }
    assert d.estado_planta == EstadoPlanta.SALUDABLE
    assert d.recomendaciones == []


def test_planta_en_riesgo_con_un_parametro_fuera_de_optimo(evaluador):
    d = evaluador.evaluar(medicion(temperatura=22, humedad=20, luz=800), perfil_cinta())  # humedad BAJO

    assert d.estados["humedad"] == EstadoParametro.BAJO
    assert d.estado_planta == EstadoPlanta.EN_RIESGO
    assert len(d.recomendaciones) == 1


def test_planta_critica_con_dos_parametros_fuera_de_optimo(evaluador):
    d = evaluador.evaluar(medicion(temperatura=22, humedad=20, luz=9000), perfil_cinta())  # humedad BAJO, luz ALTO

    assert d.estado_planta == EstadoPlanta.CRITICO
    assert len(d.recomendaciones) == 2


def test_parametros_que_el_perfil_no_conoce_se_ignoran(evaluador):
    d = evaluador.evaluar(medicion(temperatura=22, humedad=50, luz=800, ph=7.0), perfil_cinta())

    assert "ph" not in d.estados
    assert d.estado_planta == EstadoPlanta.SALUDABLE


def test_medicion_sin_ningun_parametro_evaluable_es_indeterminada(evaluador):
    # Caso real: datos históricos guardados antes de que se validara el perfil.
    d = evaluador.evaluar(medicion(ph=7.0), perfil_cinta())

    assert d.estados == {}
    assert d.estado_planta == EstadoPlanta.INDETERMINADO
    assert d.recomendaciones == []


def test_reevaluar_un_valor_historico_imposible_no_falla(evaluador):
    d = evaluador.evaluar(medicion(temperatura=9999, humedad=50, luz=800), perfil_cinta())

    assert d.estados["temperatura"] == EstadoParametro.ALTO
