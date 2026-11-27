from datetime import datetime
from typing import List
from dominio.entidades.medicion import Medicion
from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.politica_fotoperiodo import PoliticaFotoperiodo
from dominio.valores.rango_referencia import RangoReferencia


class EvaluadorFotoperiodo:
    def __init__(self, politica: PoliticaFotoperiodo = PoliticaFotoperiodo()):
        self.politica = politica

    def evaluar_luz(
        self,
        medicion_actual: Medicion,
        estado_base: EstadoParametro,
        rango_luz: RangoReferencia,
        historial_reciente: List[Medicion],
    ) -> EstadoParametro:
        # Si la luz es OPTIMA o ALTA (ej. luz artificial de noche), no se altera
        if estado_base != EstadoParametro.BAJO:
            return estado_base

        horas_oscuras = self.calcular_horas_oscuridad(
            medicion_actual, rango_luz, historial_reciente
        )

        # Regla 1: Si supera el máximo permitido en oscuridad, SIEMPRE es alerta BAJO
        if horas_oscuras >= self.politica.horas_oscuridad_maximas:
            return EstadoParametro.BAJO

        # Regla 2: Si es de noche y aún está dentro del límite, es reposo normal
        if self.politica.es_horario_nocturno(medicion_actual.fecha):
            return EstadoParametro.REPOSO_NOCTURNO

        # Regla 3: Es de día y hay poca luz
        return EstadoParametro.BAJO

    def calcular_horas_oscuridad(
        self,
        medicion_actual: Medicion,
        rango_luz: RangoReferencia,
        historial_reciente: List[Medicion],
    ) -> float:
        """
        Recorre el historial (del más reciente al más antiguo) mientras la luz
        siga por debajo del mínimo para medir cuánto tiempo lleva a oscuras.
        """
        if not historial_reciente:
            return 0.0

        fecha_actual = self._sin_tz(medicion_actual.fecha)
        inicio_oscuridad = fecha_actual

        # Ordenamos por fecha descendente para garantizar el recorrido hacia atrás
        ordenadas = sorted(
            historial_reciente,
            key=lambda m: self._sin_tz(m.fecha),
            reverse=True,
        )

        for previa in ordenadas:
            fecha_previa = self._sin_tz(previa.fecha)
            if fecha_previa >= fecha_actual:
                continue

            luz_previa = previa.valores.get("luz")
            if luz_previa is None:
                continue

            if rango_luz.evaluar(luz_previa) == EstadoParametro.BAJO:
                inicio_oscuridad = fecha_previa
            else:
                # Encontró luz suficiente: aquí se corta la racha de oscuridad
                break

        diferencia = fecha_actual - inicio_oscuridad
        return max(0.0, diferencia.total_seconds() / 3600.0)

    @staticmethod
    def _sin_tz(dt: datetime) -> datetime:
        """Evita errores al comparar fechas de SQLite (sin tz) con fechas con tz."""
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
