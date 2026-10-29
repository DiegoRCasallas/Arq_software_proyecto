"""
RangoReferencia: representa los límites de un parámetro para una especie
y sabe evaluar un valor contra sí mismo.

Diseño (ver docs/arquitectura.md, sección SOLID):
- SRP: su única razón de cambio es la fórmula de comparación de un parámetro.
- Alta cohesión: los datos (límites) y el comportamiento (evaluar) viven juntos.
- Es inmutable (frozen) porque un rango de referencia no cambia una vez definido
  para una especie; cualquier "cambio" implica crear un nuevo objeto.

Convención de límites (documentada para RF: "qué pasa en el límite exacto"):
- valor < optimo_min          -> BAJO
- optimo_min <= valor <= optimo_max -> OPTIMO   (los límites SÍ cuentan como óptimo)
- valor > optimo_max          -> ALTO

`minimo` y `maximo` en este objeto representan el rango físicamente posible
para el parámetro (ver ValorFueraDeRangoFisico), y se usan para validar antes
de clasificar, no para la clasificación BAJO/OPTIMO/ALTO en sí.
"""
from dominio.valores.estado_parametro import EstadoParametro

class RangoReferencia:
    def __init__(self, parametro: str, minimo: float, optimo_min: float, optimo_max: float, maximo: float, unidad: str = ""):
        self.parametro = parametro
        self.minimo = minimo
        self.optimo_min = optimo_min
        self.optimo_max = optimo_max
        self.maximo = maximo
        self.unidad = unidad

    def evaluar(self, valor: float):
        # Lógica de evaluación del dominio basada en los rangos
        if valor < self.optimo_min:
            return EstadoParametro.BAJO
        elif valor > self.optimo_max:
            return EstadoParametro.ALTO
        else:
            return EstadoParametro.OPTIMO
            
    def validar_fisicamente(self, valor: float) -> bool:
        return self.minimo <= valor <= self.maximo