"""
DiagnosticarPlantaUseCase: caso de uso de la capa de aplicación.

Responsabilidad (SRP): coordinar la obtención del perfil de la especie
(vía el puerto TablaReferencia) y la evaluación de la lectura (vía
EvaluadorPlanta). No contiene reglas de negocio propias -- esas viven en
el dominio -- ni conoce HTTP, JSON, ni Flask.

DIP: depende de las abstracciones TablaReferencia y EvaluadorPlanta,
inyectadas por constructor. La instancia concreta de TablaReferencia
(hoy TablaReferenciaCSV) se decide en la capa de infraestructura/arranque,
no aquí.

Nota: este caso de uso recibe una LecturaSensor y un nombre de especie ya
como tipos simples/de dominio. La validación de la entrada HTTP cruda
(dict, strings sin convertir, campos faltantes) ocurre ANTES de este
punto, en la capa de presentación (RA6).
"""
from dominio.entidades.lectura_sensor import LecturaSensor
from dominio.entidades.diagnostico_planta import DiagnosticoPlanta
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from dominio.puertos.tabla_referencia import TablaReferencia


class DiagnosticarPlantaUseCase:
    def __init__(self, tabla_referencia: TablaReferencia, evaluador: EvaluadorPlanta):
        self._tabla_referencia = tabla_referencia
        self._evaluador = evaluador

    def ejecutar(self, especie: str, lectura: LecturaSensor) -> DiagnosticoPlanta:
        perfil = self._tabla_referencia.obtener_perfil(especie)
        return self._evaluador.evaluar(lectura, perfil)
