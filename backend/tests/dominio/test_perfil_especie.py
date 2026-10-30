from datetime import datetime

import pytest

from dominio.entidades.medicion import Medicion
from dominio.excepciones.errores_dominio import (
    ParametroAusente,
    ParametroDesconocido,
    ValorFueraDeRangoFisico,
)
from tests.fakes import perfil_cinta


def medicion(**valores):
    return Medicion(planta_id=None, fecha=datetime.now(), valores=valores)


def test_medicion_completa_y_posible_es_aceptada():
    perfil_cinta().validar_medicion(medicion(temperatura=22, humedad=50, luz=800))


def test_valores_en_los_limites_fisicos_exactos_son_aceptados():
    perfil_cinta().validar_medicion(medicion(temperatura=-10, humedad=100, luz=0))
    perfil_cinta().validar_medicion(medicion(temperatura=50, humedad=0, luz=50000))


def test_valores_anomalos_pero_posibles_son_aceptados():
    # Ser "malo para la planta" no es lo mismo que ser imposible: se acepta y se diagnostica.
    perfil_cinta().validar_medicion(medicion(temperatura=45, humedad=10, luz=9000))


def test_parametro_desconocido_se_rechaza():
    with pytest.raises(ParametroDesconocido) as error:
        perfil_cinta().validar_medicion(medicion(temperatura=22, humedad=50, luz=800, ph=7.0))
    assert error.value.nombre_parametro == "ph"
    assert error.value.especie == "Cinta"


def test_medicion_solo_con_parametros_desconocidos_se_rechaza():
    with pytest.raises(ParametroDesconocido):
        perfil_cinta().validar_medicion(medicion(ph=7.0))


@pytest.mark.parametrize("faltante", ["temperatura", "humedad", "luz"])
def test_parametro_faltante_se_rechaza(faltante):
    valores = {"temperatura": 22, "humedad": 50, "luz": 800}
    del valores[faltante]
    with pytest.raises(ParametroAusente) as error:
        perfil_cinta().validar_medicion(medicion(**valores))
    assert error.value.nombre_parametro == faltante


@pytest.mark.parametrize("parametro,valor", [
    ("temperatura", 9999), ("temperatura", -11), ("humedad", 100.5), ("humedad", -1), ("luz", 50001),
])
def test_valor_fisicamente_imposible_se_rechaza(parametro, valor):
    valores = {"temperatura": 22, "humedad": 50, "luz": 800}
    valores[parametro] = valor
    with pytest.raises(ValorFueraDeRangoFisico) as error:
        perfil_cinta().validar_medicion(medicion(**valores))
    assert error.value.nombre_parametro == parametro
