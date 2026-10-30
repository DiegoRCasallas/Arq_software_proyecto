import pytest

from dominio.excepciones.errores_dominio import EspecieNoEncontrada
from infraestructura.persistencia.sql.tabla_referencia_sql import TablaReferenciaSQL


@pytest.fixture
def tabla(app):
    with app.app_context():
        yield TablaReferenciaSQL()


def test_obtener_perfil_existente(tabla):
    perfil = tabla.obtener_perfil("Cinta")

    assert perfil.nombre_especie == "Cinta"
    assert set(perfil.rangos) == {"temperatura", "humedad", "luz"}
    assert perfil.rangos["temperatura"].minimo == -10      # límites físicos, no de tolerancia
    assert perfil.rangos["temperatura"].maximo == 50


def test_obtener_perfil_es_insensible_a_mayusculas_y_espacios(tabla):
    assert tabla.obtener_perfil("  cinta  ").nombre_especie == "Cinta"
    assert tabla.obtener_perfil("ALBAHACA").nombre_especie == "albahaca"


def test_especie_inexistente_lanza_excepcion_de_dominio_y_no_devuelve_none(tabla):
    with pytest.raises(EspecieNoEncontrada):
        tabla.obtener_perfil("dinosaurio")


def test_listar_especies_contiene_al_menos_cinco_especies(tabla):
    perfiles = tabla.listar_especies()
    assert len(perfiles) >= 5
    nombres = [p.nombre_especie for p in perfiles]
    assert "Cinta" in nombres
    for perfil in perfiles:
        assert set(perfil.rangos) == {"temperatura", "humedad", "luz"}
