from dominio.entidades.lectura_sensor import Medicion
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.entidades.diagnostico_planta import DiagnosticoPlanta

class EvaluadorPlanta:
    def __init__(self, estrategia, generador):
        self.estrategia = estrategia
        self.generador = generador

    def evaluar(self, medicion: Medicion, perfil: PerfilEspecie) -> DiagnosticoPlanta:
        estados = {}
        
        # 1. Evaluamos dinámicamente cada parámetro que llegó del sensor
        for parametro, valor in medicion.valores.items():
            if parametro in perfil.rangos:
                rango = perfil.rangos[parametro]
                # El rango sabe cómo evaluarse a sí mismo retornando un EstadoParametro (ALTO, BAJO, OPTIMO)
                estados[parametro] = rango.evaluar(valor)

        # 2. Delegamos a las estrategias el cálculo final
        estado_general = self.estrategia.calcular(estados)
        recomendaciones = self.generador.generar(estados)

        # 3. Retornamos la entidad pura de diagnóstico
        return DiagnosticoPlanta(
            estados=estados,
            estado_planta=estado_general,
            recomendaciones=recomendaciones
        )