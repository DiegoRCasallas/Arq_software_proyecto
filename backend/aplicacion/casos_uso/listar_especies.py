"""
ListarEspeciesUseCase: caso de uso para RF5 (consultar especies soportadas
y sus rangos de referencia).

Igual que DiagnosticarPlantaUseCase, solo orquesta: delega en el puerto
TablaReferencia y no conoce cómo se serializa la respuesta a JSON
(eso es responsabilidad de la capa de presentación).
"""
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.puertos.tabla_referencia import TablaReferencia


class ListarEspeciesUseCase:
    def __init__(self, tabla_referencia: TablaReferencia):
        self._tabla_referencia = tabla_referencia

    def ejecutar(self) -> list[PerfilEspecie]:
        return self._tabla_referencia.listar_especies()
