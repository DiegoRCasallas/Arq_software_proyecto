from pathlib import Path

import pytest

from infraestructura.persistencia.tabla_referencia_csv import TablaReferenciaCSV
from dominio.excepciones.errores_dominio import EspecieNoEncontrada

RUTA_CSV = Path(__file__).parent.parent.parent / "infraestructura" / "persistencia" / "especies.csv"


@pytest.fixture
def tabla():
    return TablaReferenciaCSV(RUTA_CSV)


def test_carga_al_menos_cinco_especies(tabla):
    assert len(tabla.listar_especies()) >= 5


def test_obtener_perfil_existente(tabla):
    perfil = tabla.obtener_perfil("albahaca")
    assert perfil.nombre_especie == "albahaca"
    assert perfil.rango_humedad.optimo_min == 40
    assert perfil.rango_humedad.optimo_max == 70


def test_obtener_perfil_es_insensible_a_mayusculas_y_espacios(tabla):
    perfil = tabla.obtener_perfil("  ALBAHACA  ")
    assert perfil.nombre_especie == "albahaca"


def test_especie_inexistente_lanza_excepcion(tabla):
    with pytest.raises(EspecieNoEncontrada):
        tabla.obtener_perfil("dinosaurio")


def test_todas_las_especies_tienen_los_tres_rangos(tabla):
    for perfil in tabla.listar_especies():
        assert perfil.rango_humedad is not None
        assert perfil.rango_luz is not None
        assert perfil.rango_temperatura is not None
