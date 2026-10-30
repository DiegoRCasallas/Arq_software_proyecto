from aplicacion.casos_uso.listar_especies import ListarEspeciesUseCase
from tests.fakes import TablaReferenciaFake, perfil_cinta


def test_lista_todas_las_especies_disponibles():
    caso_de_uso = ListarEspeciesUseCase(tabla_referencia=TablaReferenciaFake({"cinta": perfil_cinta()}))

    especies = caso_de_uso.ejecutar()

    assert len(especies) == 1
    assert especies[0].nombre_especie == "Cinta"


def test_lista_vacia_cuando_no_hay_especies():
    caso_de_uso = ListarEspeciesUseCase(tabla_referencia=TablaReferenciaFake({}))

    assert caso_de_uso.ejecutar() == []
