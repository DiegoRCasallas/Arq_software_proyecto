"""
DiagnosticoPlanta: resultado completo de evaluar una lectura contra un perfil
de especie. Es lo que devuelve EvaluadorPlanta y lo que la capa de
presentación traduce a JSON.
"""
from dataclasses import dataclass, field

from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.indice_vitalidad import IndiceVitalidad


@dataclass(frozen=True)
class DiagnosticoPlanta:
    estado_humedad: EstadoParametro
    estado_luz: EstadoParametro
    estado_temperatura: EstadoParametro
    indice_vitalidad: IndiceVitalidad
    recomendaciones: list[str] = field(default_factory=list)

    def como_diccionario_estados(self) -> dict[str, EstadoParametro]:
        """Utilidad para que la estrategia de agregación y las recomendaciones
        trabajen sobre un mapeo nombre -> estado, sin acoplarse a los nombres
        de los atributos individuales."""
        return {
            "humedad": self.estado_humedad,
            "luz": self.estado_luz,
            "temperatura": self.estado_temperatura,
        }
