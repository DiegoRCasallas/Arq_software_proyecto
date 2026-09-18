"""
EvaluadorPlanta: orquesta el diagnóstico completo de una planta.

Responsabilidad única (SRP): coordinar la evaluación de los tres
parámetros, delegar el cálculo del índice de vitalidad a la estrategia
de agregación inyectada, y delegar la redacción de recomendaciones al
GeneradorRecomendaciones. No conoce CÓMO se compara un valor (eso lo
resuelve RangoReferencia) ni CÓMO se agregan los estados (eso lo resuelve
la estrategia inyectada) ni CÓMO se accede a la tabla de referencia (eso
lo resuelve el puerto TablaReferencia, usado en la capa de aplicación).

DIP: depende de la abstracción EstrategiaAgregacionVitalidad, inyectada
por constructor, no de una implementación concreta.
"""
from dominio.entidades.lectura_sensor import LecturaSensor
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.entidades.diagnostico_planta import DiagnosticoPlanta
from dominio.puertos.estrategia_agregacion_vitalidad import EstrategiaAgregacionVitalidad
from dominio.servicios.generador_recomendaciones import GeneradorRecomendaciones


class EvaluadorPlanta:
    def __init__(
        self,
        estrategia_agregacion: EstrategiaAgregacionVitalidad,
        generador_recomendaciones: GeneradorRecomendaciones | None = None,
    ):
        self._estrategia = estrategia_agregacion
        self._generador_recomendaciones = generador_recomendaciones or GeneradorRecomendaciones()

    def evaluar(self, lectura: LecturaSensor, perfil: PerfilEspecie) -> DiagnosticoPlanta:
        estado_humedad = perfil.rango_humedad.evaluar(lectura.humedad)
        estado_luz = perfil.rango_luz.evaluar(lectura.luz)
        estado_temperatura = perfil.rango_temperatura.evaluar(lectura.temperatura)

        estados = {
            "humedad": estado_humedad,
            "luz": estado_luz,
            "temperatura": estado_temperatura,
        }

        indice = self._estrategia.calcular(estados)
        recomendaciones = self._generador_recomendaciones.generar(estados)

        return DiagnosticoPlanta(
            estado_humedad=estado_humedad,
            estado_luz=estado_luz,
            estado_temperatura=estado_temperatura,
            indice_vitalidad=indice,
            recomendaciones=recomendaciones,
        )
