import dataclasses

import pytest

from dominio.valores.rango_referencia import RangoReferencia
from dominio.valores.estado_parametro import EstadoParametro


@pytest.fixture
def rango_humedad():
    # físico [0, 100], óptimo [40, 70]
    return RangoReferencia(parametro="humedad", minimo=0, optimo_min=40, optimo_max=70, maximo=100)


def test_valor_por_debajo_del_optimo_es_bajo(rango_humedad):
    assert rango_humedad.evaluar(30) == EstadoParametro.BAJO


def test_valor_en_el_limite_inferior_del_optimo_es_optimo(rango_humedad):
    assert rango_humedad.evaluar(40) == EstadoParametro.OPTIMO


def test_valor_dentro_del_optimo_es_optimo(rango_humedad):
    assert rango_humedad.evaluar(55) == EstadoParametro.OPTIMO


def test_valor_en_el_limite_superior_del_optimo_es_optimo(rango_humedad):
    assert rango_humedad.evaluar(70) == EstadoParametro.OPTIMO


def test_valor_por_encima_del_optimo_es_alto(rango_humedad):
    assert rango_humedad.evaluar(85) == EstadoParametro.ALTO


def test_evaluar_es_tolerante_y_clasifica_incluso_valores_imposibles(rango_humedad):
    # Rechazar lecturas imposibles es tarea de PerfilEspecie.validar_medicion;
    # evaluar() no debe fallar al reevaluar datos históricos.
    assert rango_humedad.evaluar(150) == EstadoParametro.ALTO
    assert rango_humedad.evaluar(-5) == EstadoParametro.BAJO


@pytest.mark.parametrize("valor", [0, 55, 100])
def test_valores_dentro_del_rango_fisico_son_validos(rango_humedad, valor):
    assert rango_humedad.validar_fisicamente(valor) is True


@pytest.mark.parametrize("valor", [-0.1, 100.1, 500])
def test_valores_fuera_del_rango_fisico_son_invalidos(rango_humedad, valor):
    assert rango_humedad.validar_fisicamente(valor) is False


def test_rango_es_inmutable(rango_humedad):
    with pytest.raises(dataclasses.FrozenInstanceError):
        rango_humedad.optimo_min = 10


@pytest.mark.parametrize("limites", [
    (0, 80, 70, 100),    # optimo_min > optimo_max
    (50, 40, 70, 100),   # minimo > optimo_min
    (0, 40, 70, 60),     # maximo < optimo_max
])
def test_rango_con_limites_incoherentes_lanza_value_error(limites):
    minimo, optimo_min, optimo_max, maximo = limites
    with pytest.raises(ValueError):
        RangoReferencia("humedad", minimo, optimo_min, optimo_max, maximo)
