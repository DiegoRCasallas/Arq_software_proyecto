import pytest

from dominio.excepciones.errores_dominio import EspecieNoEncontrada
from infraestructura.persistencia.csv.tabla_referencia_csv import TablaReferenciaCSV


@pytest.fixture
def tabla():
    return TablaReferenciaCSV()  # usa el CSV real, ubicado por ruta relativa al módulo


def test_carga_al_menos_cinco_especies(tabla):
    assert len(tabla.listar_especies()) >= 5


def test_obtener_perfil_existente(tabla):
    perfil = tabla.obtener_perfil("albahaca")

    assert perfil.nombre_especie == "albahaca"
    assert perfil.rangos["humedad"].optimo_min == 40
    assert perfil.rangos["humedad"].optimo_max == 70


def test_obtener_perfil_es_insensible_a_mayusculas_y_espacios(tabla):
    assert tabla.obtener_perfil("  ALBAHACA  ").nombre_especie == "albahaca"


def test_incluye_la_especie_de_la_planta_de_prueba(tabla):
    # Con TIPO_PERSISTENCIA=CSV la planta sembrada ("Cinta") debe seguir funcionando.
    assert tabla.obtener_perfil("Cinta").rangos["temperatura"].optimo_max == 24


def test_especie_inexistente_lanza_excepcion_de_dominio(tabla):
    with pytest.raises(EspecieNoEncontrada):
        tabla.obtener_perfil("dinosaurio")


def test_todas_las_especies_tienen_los_mismos_parametros(tabla):
    for perfil in tabla.listar_especies():
        assert set(perfil.rangos) == {"humedad", "luz", "temperatura"}


def test_la_ruta_no_depende_del_directorio_de_trabajo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert TablaReferenciaCSV().obtener_perfil("poto").nombre_especie == "poto"
