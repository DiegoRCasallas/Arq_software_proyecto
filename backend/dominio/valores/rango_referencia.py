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
