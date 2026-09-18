from aplicacion.casos_uso.listar_especies import ListarEspeciesUseCase
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.valores.rango_referencia import RangoReferencia
from tests.aplicacion.test_diagnosticar_planta import TablaReferenciaFake


def test_lista_todas_las_especies_disponibles():
    perfil = PerfilEspecie(
        nombre_especie="poto",
        rango_humedad=RangoReferencia("humedad", 0, 30, 60, 100),
        rango_luz=RangoReferencia("luz", 0, 1000, 10000, 30000),
        rango_temperatura=RangoReferencia("temperatura", -5, 15, 29, 45),
    )
    tabla_fake = TablaReferenciaFake({"poto": perfil})
    caso_de_uso = ListarEspeciesUseCase(tabla_referencia=tabla_fake)

    especies = caso_de_uso.ejecutar()

    assert len(especies) == 1
    assert especies[0].nombre_especie == "poto"


def test_lista_vacia_cuando_no_hay_especies():
    tabla_fake = TablaReferenciaFake({})
    caso_de_uso = ListarEspeciesUseCase(tabla_referencia=tabla_fake)

    assert caso_de_uso.ejecutar() == []
