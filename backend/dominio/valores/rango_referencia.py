"""
RangoReferencia: representa los límites de un parámetro para una especie
y sabe evaluar un valor contra sí mismo.

Diseño:
- SRP: su única razón de cambio es la fórmula de comparación de un parámetro.
- Alta cohesión: los datos (límites) y el comportamiento (evaluar) viven juntos.
- Es inmutable (frozen): un rango de referencia no cambia una vez definido
  para una especie; cualquier "cambio" implica crear un nuevo objeto.
- Invariante: minimo <= optimo_min <= optimo_max <= maximo. Un rango mal
  cargado (CSV o BD con datos corruptos) se rechaza al construirlo, en lugar
  de producir diagnósticos incoherentes más tarde.

Significado de cada límite (misma semántica en CSV, BD y seed):
- minimo / maximo: rango FÍSICAMENTE POSIBLE del parámetro. Un valor fuera de
  él no es "una planta en mal estado" sino una lectura imposible (sensor
  defectuoso, dato corrupto) y se rechaza (ver validar_fisicamente).
- optimo_min / optimo_max: rango ideal para la especie.

Convención de límites en la clasificación:
- valor < optimo_min                -> BAJO
- optimo_min <= valor <= optimo_max -> OPTIMO   (los límites SÍ cuentan como óptimo)
- valor > optimo_max                -> ALTO

evaluar() es deliberadamente tolerante: clasifica cualquier número. Rechazar
lecturas imposibles es responsabilidad de PerfilEspecie.validar_medicion al
registrar una medición; así, reevaluar datos históricos nunca falla.
"""
from dataclasses import dataclass

from dominio.valores.estado_parametro import EstadoParametro


@dataclass(frozen=True)
class RangoReferencia:
    parametro: str
    minimo: float
    optimo_min: float
    optimo_max: float
    maximo: float
    unidad: str = ""

    def __post_init__(self):
        if not (self.minimo <= self.optimo_min <= self.optimo_max <= self.maximo):
            raise ValueError(
                f"Rango inválido para '{self.parametro}': se esperaba "
                f"minimo <= optimo_min <= optimo_max <= maximo, pero se recibió "
                f"({self.minimo}, {self.optimo_min}, {self.optimo_max}, {self.maximo})."
            )

    def evaluar(self, valor: float) -> EstadoParametro:
        if valor < self.optimo_min:
            return EstadoParametro.BAJO
        if valor > self.optimo_max:
            return EstadoParametro.ALTO
        return EstadoParametro.OPTIMO

    def validar_fisicamente(self, valor: float) -> bool:
        return self.minimo <= valor <= self.maximo
