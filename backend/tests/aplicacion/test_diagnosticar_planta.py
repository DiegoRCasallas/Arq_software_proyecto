import pytest

from aplicacion.casos_uso.diagnosticar_planta import DiagnosticarPlantaUseCase
from dominio.entidades.lectura_sensor import LecturaSensor
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.valores.rango_referencia import RangoReferencia
from dominio.valores.indice_vitalidad import IndiceVitalidad
from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from dominio.excepciones.errores_dominio import EspecieNoEncontrada


class TablaReferenciaFake:
    """Doble de prueba: implementa el mismo contrato que TablaReferenciaCSV
    (LSP) pero sin leer ningún archivo, para que estas pruebas sean rápidas
    y no dependan de infraestructura."""

    def __init__(self, perfiles: dict[str, PerfilEspecie]):
        self._perfiles = perfiles

    def obtener_perfil(self, especie: str) -> PerfilEspecie:
        perfil = self._perfiles.get(especie.lower())
        if perfil is None:
            raise EspecieNoEncontrada(especie)
        return perfil

    def listar_especies(self) -> list[PerfilEspecie]:
        return list(self._perfiles.values())


@pytest.fixture
def perfil_albahaca():
    return PerfilEspecie(
        nombre_especie="albahaca",
        rango_humedad=RangoReferencia("humedad", 0, 40, 70, 100),
        rango_luz=RangoReferencia("luz", 0, 8000, 20000, 50000),
        rango_temperatura=RangoReferencia("temperatura", -10, 18, 27, 50),
    )


@pytest.fixture
def caso_de_uso(perfil_albahaca):
    tabla_fake = TablaReferenciaFake({"albahaca": perfil_albahaca})
    evaluador = EvaluadorPlanta(estrategia_agregacion=EstrategiaAgregacionPorConteo())
    return DiagnosticarPlantaUseCase(tabla_referencia=tabla_fake, evaluador=evaluador)


def test_diagnostica_planta_saludable(caso_de_uso):
    lectura = LecturaSensor(humedad=55, luz=12000, temperatura=22)
    diagnostico = caso_de_uso.ejecutar("albahaca", lectura)
    assert diagnostico.indice_vitalidad == IndiceVitalidad.SALUDABLE


def test_diagnostica_planta_en_riesgo(caso_de_uso):
    lectura = LecturaSensor(humedad=20, luz=12000, temperatura=22)
    diagnostico = caso_de_uso.ejecutar("albahaca", lectura)
    assert diagnostico.indice_vitalidad == IndiceVitalidad.EN_RIESGO


def test_especie_desconocida_propaga_excepcion_de_dominio(caso_de_uso):
    lectura = LecturaSensor(humedad=55, luz=12000, temperatura=22)
    with pytest.raises(EspecieNoEncontrada):
        caso_de_uso.ejecutar("dinosaurio", lectura)
