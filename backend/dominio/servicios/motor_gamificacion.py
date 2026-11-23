from dataclasses import dataclass
from typing import Optional
from dominio.entidades.diagnostico_planta import DiagnosticoPlanta
from dominio.valores.estado_animo import EstadoAnimo
from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.estado_planta import EstadoPlanta

@dataclass(frozen=True)
class ResultadoGamificacion:
    delta_xp: int
    estado_animo: EstadoAnimo
    motivo: str

class MotorGamificacion:
    XP_RIEGO_EXITOSO = 50
    XP_MEDICION_OPTIMA = 10
    XP_PENALIZACION_RIESGO = -10
    XP_PENALIZACION_CRITICA = -20

    def calcular(
        self,
        diagnostico_actual: DiagnosticoPlanta,
        diagnostico_anterior: Optional[DiagnosticoPlanta] = None,
    ) -> ResultadoGamificacion:
        animo = self._determinar_animo(diagnostico_actual)

        # 1. Recompensa especial: el usuario regó la planta (humedad pasó de BAJO a OPTIMO)
        if diagnostico_anterior:
            hum_anterior = diagnostico_anterior.estados.get("humedad")
            hum_actual = diagnostico_actual.estados.get("humedad")
            if hum_anterior == EstadoParametro.BAJO and hum_actual == EstadoParametro.OPTIMO:
                return ResultadoGamificacion(
                    delta_xp=self.XP_RIEGO_EXITOSO,
                    estado_animo=animo,
                    motivo="¡Riego detectado! La humedad volvió al rango óptimo.",
                )

        # 2. Evaluación general según estado de la planta
        if diagnostico_actual.estado_planta == EstadoPlanta.SALUDABLE:
            return ResultadoGamificacion(
                delta_xp=self.XP_MEDICION_OPTIMA,
                estado_animo=EstadoAnimo.FELIZ,
                motivo="Parámetros en rango óptimo.",
            )

        if diagnostico_actual.estado_planta == EstadoPlanta.CRITICO:
            return ResultadoGamificacion(
                delta_xp=self.XP_PENALIZACION_CRITICA,
                estado_animo=animo,
                motivo="La planta está en estado crítico.",
            )

        return ResultadoGamificacion(
            delta_xp=self.XP_PENALIZACION_RIESGO,
            estado_animo=animo,
            motivo="Algunos parámetros están fuera del rango ideal.",
        )

    def _determinar_animo(self, diagnostico: DiagnosticoPlanta) -> EstadoAnimo:
        if diagnostico.estado_planta == EstadoPlanta.SALUDABLE:
            return EstadoAnimo.FELIZ

        estados = diagnostico.estados
        # Prioridad visual de alertas
        if estados.get("humedad") == EstadoParametro.BAJO:
            return EstadoAnimo.SEDIENTA
        if estados.get("temperatura") == EstadoParametro.ALTO:
            return EstadoAnimo.SOFOCADA
        if estados.get("temperatura") == EstadoParametro.BAJO:
            return EstadoAnimo.CON_FRIO
        if estados.get("luz") == EstadoParametro.BAJO:
            return EstadoAnimo.SIN_LUZ

        return EstadoAnimo.EN_RIESGO
