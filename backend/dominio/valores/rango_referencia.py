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
from dataclasses import dataclass

from dominio.valores.estado_parametro import EstadoParametro
from dominio.excepciones.errores_dominio import ValorFueraDeRangoFisico


@dataclass(frozen=True)
class RangoReferencia:
    nombre_parametro: str  # "humedad", "luz" o "temperatura" (útil para mensajes de error)
    minimo: float          # límite físicamente posible inferior
    optimo_min: float
    optimo_max: float
    maximo: float           # límite físicamente posible superior

    def __post_init__(self):
        if not (self.minimo <= self.optimo_min <= self.optimo_max <= self.maximo):
            raise ValueError(
                f"Rango de referencia inválido para '{self.nombre_parametro}': "
                f"se debe cumplir minimo <= optimo_min <= optimo_max <= maximo "
                f"(recibido: {self.minimo}, {self.optimo_min}, {self.optimo_max}, {self.maximo})."
            )

    def validar_fisicamente(self, valor: float) -> None:
        """Lanza ValorFueraDeRangoFisico si el valor no es físicamente posible."""
        if valor < self.minimo or valor > self.maximo:
            raise ValorFueraDeRangoFisico(
                nombre_parametro=self.nombre_parametro,
                valor=valor,
                minimo_fisico=self.minimo,
                maximo_fisico=self.maximo,
            )

    def evaluar(self, valor: float) -> EstadoParametro:
        """
        Clasifica un valor ya validado físicamente como BAJO, OPTIMO o ALTO
        según los límites óptimos de este rango.
        """
        self.validar_fisicamente(valor)
        if valor < self.optimo_min:
            return EstadoParametro.BAJO
        if valor > self.optimo_max:
            return EstadoParametro.ALTO
        return EstadoParametro.OPTIMO
