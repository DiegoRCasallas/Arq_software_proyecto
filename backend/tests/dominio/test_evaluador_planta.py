import pytest

from dominio.entidades.lectura_sensor import LecturaSensor
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.valores.rango_referencia import RangoReferencia
from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.indice_vitalidad import IndiceVitalidad
from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from dominio.excepciones.errores_dominio import ValorFueraDeRangoFisico


@pytest.fixture
def perfil_albahaca():
    return PerfilEspecie(
        nombre_especie="albahaca",
        rango_humedad=RangoReferencia("humedad", 0, 40, 70, 100),
        rango_luz=RangoReferencia("luz", 0, 8000, 20000, 50000),
        rango_temperatura=RangoReferencia("temperatura", -10, 18, 27, 50),
    )


@pytest.fixture
def evaluador():
    return EvaluadorPlanta(estrategia_agregacion=EstrategiaAgregacionPorConteo())


def test_planta_saludable_cuando_todo_esta_en_optimo(evaluador, perfil_albahaca):
    lectura = LecturaSensor(humedad=55, luz=12000, temperatura=22)
    diagnostico = evaluador.evaluar(lectura, perfil_albahaca)

    assert diagnostico.estado_humedad == EstadoParametro.OPTIMO
    assert diagnostico.estado_luz == EstadoParametro.OPTIMO
    assert diagnostico.estado_temperatura == EstadoParametro.OPTIMO
    assert diagnostico.indice_vitalidad == IndiceVitalidad.SALUDABLE
    assert diagnostico.recomendaciones == []


def test_planta_en_riesgo_con_un_parametro_fuera_de_optimo(evaluador, perfil_albahaca):
    lectura = LecturaSensor(humedad=20, luz=12000, temperatura=22)  # humedad BAJO
    diagnostico = evaluador.evaluar(lectura, perfil_albahaca)

    assert diagnostico.estado_humedad == EstadoParametro.BAJO
    assert diagnostico.indice_vitalidad == IndiceVitalidad.EN_RIESGO
    assert len(diagnostico.recomendaciones) == 1


def test_planta_critica_con_dos_parametros_fuera_de_optimo(evaluador, perfil_albahaca):
    lectura = LecturaSensor(humedad=20, luz=45000, temperatura=22)  # humedad BAJO, luz ALTO
    diagnostico = evaluador.evaluar(lectura, perfil_albahaca)

    assert diagnostico.indice_vitalidad == IndiceVitalidad.CRITICO
    assert len(diagnostico.recomendaciones) == 2


def test_valor_fisicamente_invalido_propaga_excepcion(evaluador, perfil_albahaca):
    lectura = LecturaSensor(humedad=500, luz=12000, temperatura=22)  # humedad imposible
    with pytest.raises(ValorFueraDeRangoFisico):
        evaluador.evaluar(lectura, perfil_albahaca)
