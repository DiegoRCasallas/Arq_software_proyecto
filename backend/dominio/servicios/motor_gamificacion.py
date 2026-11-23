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


@dataclass(frozen=True)
class ResultadoMinijuego:
    xp_otorgada: int
    xp_restante_hoy: int
    tope_diario_alcanzado: bool


class MotorGamificacion:
    XP_RIEGO_EXITOSO = 50
    XP_MEDICION_OPTIMA = 10
    XP_PENALIZACION_RIESGO = -10
    XP_PENALIZACION_CRITICA = -20

    # Reglas del minijuego (el frontend nunca decide la XP)
    PUNTOS_POR_XP = 5
    TOPE_XP_POR_PARTIDA = 30
    TOPE_XP_DIARIO_MINIJUEGO = 60

    def calcular(
        self,
        diagnostico_actual: DiagnosticoPlanta,
        diagnostico_anterior: Optional[DiagnosticoPlanta] = None,
    ) -> ResultadoGamificacion:
        animo = self._determinar_animo(diagnostico_actual)

        if diagnostico_anterior:
            hum_anterior = diagnostico_anterior.estados.get("humedad")
            hum_actual = diagnostico_actual.estados.get("humedad")
            if hum_anterior == EstadoParametro.BAJO and hum_actual == EstadoParametro.OPTIMO:
                return ResultadoGamificacion(
                    delta_xp=self.XP_RIEGO_EXITOSO,
                    estado_animo=animo,
                    motivo="¡Riego detectado! La humedad volvió al rango óptimo.",
                )

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

    def calcular_xp_minijuego(self, puntaje: int, xp_ganada_hoy: int) -> ResultadoMinijuego:
        if puntaje < 0:
            raise ValueError("El puntaje no puede ser negativo")

        xp_disponible = max(0, self.TOPE_XP_DIARIO_MINIJUEGO - xp_ganada_hoy)
        if xp_disponible == 0:
            return ResultadoMinijuego(
                xp_otorgada=0,
                xp_restante_hoy=0,
                tope_diario_alcanzado=True,
            )

        xp_bruta = min(puntaje // self.PUNTOS_POR_XP, self.TOPE_XP_POR_PARTIDA)
        xp_otorgada = min(xp_bruta, xp_disponible)
        xp_restante = xp_disponible - xp_otorgada

        return ResultadoMinijuego(
            xp_otorgada=xp_otorgada,
            xp_restante_hoy=xp_restante,
            tope_diario_alcanzado=(xp_restante == 0),
        )

    def _determinar_animo(self, diagnostico: DiagnosticoPlanta) -> EstadoAnimo:
        if diagnostico.estado_planta == EstadoPlanta.SALUDABLE:
            return EstadoAnimo.FELIZ

        estados = diagnostico.estados
        # Prioridad visual: agua -> temperatura -> luz
        if estados.get("humedad") == EstadoParametro.BAJO:
            return EstadoAnimo.SEDIENTA
        if estados.get("humedad") == EstadoParametro.ALTO:
            return EstadoAnimo.AHOGADA
        if estados.get("temperatura") == EstadoParametro.ALTO:
            return EstadoAnimo.SOFOCADA
        if estados.get("temperatura") == EstadoParametro.BAJO:
            return EstadoAnimo.CON_FRIO
        if estados.get("luz") == EstadoParametro.BAJO:
            return EstadoAnimo.SIN_LUZ
        if estados.get("luz") == EstadoParametro.ALTO:
            return EstadoAnimo.DESLUMBRADA

        return EstadoAnimo.EN_RIESGO
