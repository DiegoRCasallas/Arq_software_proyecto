from typing import List, Optional
from dominio.entidades.medicion import Medicion
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.entidades.diagnostico_planta import DiagnosticoPlanta
from dominio.servicios.evaluador_fotoperiodo import EvaluadorFotoperiodo


class EvaluadorPlanta:
    def __init__(self, estrategia, generador, evaluador_fotoperiodo=None):
        self.estrategia = estrategia
        self.generador = generador
        self.evaluador_fotoperiodo = evaluador_fotoperiodo or EvaluadorFotoperiodo()

    def evaluar(
        self,
        medicion: Medicion,
        perfil: PerfilEspecie,
        historial_reciente: Optional[List[Medicion]] = None,
    ) -> DiagnosticoPlanta:
        estados = {}

        # 1. Evaluamos dinámicamente cada parámetro que llegó del sensor
        for parametro, valor in medicion.valores.items():
            if parametro in perfil.rangos:
                rango = perfil.rangos[parametro]
                estados[parametro] = rango.evaluar(valor)

        # 2. Ajuste de luz según horario nocturno y horas acumuladas en oscuridad
        if "luz" in estados and "luz" in perfil.rangos:
            estados["luz"] = self.evaluador_fotoperiodo.evaluar_luz(
                medicion_actual=medicion,
                estado_base=estados["luz"],
                rango_luz=perfil.rangos["luz"],
                historial_reciente=historial_reciente or [],
            )

        # 3. Delegamos a las estrategias el cálculo final
        estado_general = self.estrategia.calcular(estados)
        recomendaciones = self.generador.generar(estados)

        # 4. Retornamos la entidad pura de diagnóstico
        return DiagnosticoPlanta(
            estados=estados,
            estado_planta=estado_general,
            recomendaciones=recomendaciones,
        )
