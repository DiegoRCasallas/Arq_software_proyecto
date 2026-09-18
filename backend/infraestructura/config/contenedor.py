"""
Composition root: aquí, y solo aquí, se decide QUÉ implementación
concreta usa cada abstracción (DIP en acción).

Si mañana se reemplaza TablaReferenciaCSV por TablaReferenciaBaseDatos,
el único cambio necesario en todo el proyecto es esta función.
"""
from pathlib import Path

from infraestructura.persistencia.tabla_referencia_csv import TablaReferenciaCSV
from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from aplicacion.casos_uso.diagnosticar_planta import DiagnosticarPlantaUseCase
from aplicacion.casos_uso.listar_especies import ListarEspeciesUseCase

_RUTA_CSV_ESPECIES = Path(__file__).parent.parent / "persistencia" / "especies.csv"


class Contenedor:
    """Agrupa las instancias ya conectadas, listas para inyectar en los
    controladores. Un enfoque simple de inyección de dependencias manual,
    suficiente para el tamaño de este proyecto."""

    def __init__(self):
        self.tabla_referencia = TablaReferenciaCSV(_RUTA_CSV_ESPECIES)
        estrategia = EstrategiaAgregacionPorConteo()
        self.evaluador_planta = EvaluadorPlanta(estrategia_agregacion=estrategia)

        self.diagnosticar_planta_use_case = DiagnosticarPlantaUseCase(
            tabla_referencia=self.tabla_referencia,
            evaluador=self.evaluador_planta,
        )
        self.listar_especies_use_case = ListarEspeciesUseCase(
            tabla_referencia=self.tabla_referencia,
        )
