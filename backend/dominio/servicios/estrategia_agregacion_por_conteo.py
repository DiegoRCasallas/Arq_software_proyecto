from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.estado_planta import EstadoPlanta

class EstrategiaAgregacionPorConteo:
    ESTADOS_NORMALES = {EstadoParametro.OPTIMO, EstadoParametro.REPOSO_NOCTURNO}

    def calcular(self, estados: dict[str, EstadoParametro]) -> EstadoPlanta:
        if not estados:
            return EstadoPlanta.INDETERMINADO

        fuera_de_optimo = sum(
            1 for estado in estados.values() if estado not in self.ESTADOS_NORMALES
        )

        if fuera_de_optimo == 0:
            return EstadoPlanta.SALUDABLE
        if fuera_de_optimo == 1:
            return EstadoPlanta.EN_RIESGO
        return EstadoPlanta.CRITICO
