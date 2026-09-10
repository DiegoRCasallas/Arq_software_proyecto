from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.estado_planta import EstadoPlanta

estrategia = EstrategiaAgregacionPorConteo()


def test_todos_optimos_es_saludable():
    estados = {
        "humedad": EstadoParametro.OPTIMO,
        "luz": EstadoParametro.OPTIMO,
        "temperatura": EstadoParametro.OPTIMO,
    }
    assert estrategia.calcular(estados) == EstadoPlanta.SALUDABLE


def test_un_parametro_fuera_de_optimo_es_en_riesgo():
    estados = {
        "humedad": EstadoParametro.BAJO,
        "luz": EstadoParametro.OPTIMO,
        "temperatura": EstadoParametro.OPTIMO,
    }
    assert estrategia.calcular(estados) == EstadoPlanta.EN_RIESGO


def test_dos_parametros_fuera_de_optimo_es_critico():
    estados = {
        "humedad": EstadoParametro.BAJO,
        "luz": EstadoParametro.ALTO,
        "temperatura": EstadoParametro.OPTIMO,
    }
    assert estrategia.calcular(estados) == EstadoPlanta.CRITICO


def test_tres_parametros_fuera_de_optimo_es_critico():
    estados = {
        "humedad": EstadoParametro.BAJO,
        "luz": EstadoParametro.ALTO,
        "temperatura": EstadoParametro.BAJO,
    }
    assert estrategia.calcular(estados) == EstadoPlanta.CRITICO
