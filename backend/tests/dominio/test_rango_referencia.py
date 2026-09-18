import pytest

from dominio.valores.rango_referencia import RangoReferencia
from dominio.valores.estado_parametro import EstadoParametro
from dominio.excepciones.errores_dominio import ValorFueraDeRangoFisico


@pytest.fixture
def rango_humedad():
    # físico [0, 100], óptimo [40, 70]
    return RangoReferencia(
        nombre_parametro="humedad", minimo=0, optimo_min=40, optimo_max=70, maximo=100
    )


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


def test_valor_fuera_del_rango_fisico_lanza_excepcion(rango_humedad):
    with pytest.raises(ValorFueraDeRangoFisico):
        rango_humedad.evaluar(150)


def test_valor_fuera_del_rango_fisico_por_debajo_lanza_excepcion(rango_humedad):
    with pytest.raises(ValorFueraDeRangoFisico):
        rango_humedad.evaluar(-5)


def test_rango_invalido_lanza_value_error():
    with pytest.raises(ValueError):
        RangoReferencia(nombre_parametro="humedad", minimo=0, optimo_min=80, optimo_max=70, maximo=100)
