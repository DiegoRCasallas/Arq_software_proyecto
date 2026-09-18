"""
EstrategiaAgregacionPorConteo: implementación por defecto de la regla de
agregación del índice de vitalidad (RF3).

Regla elegida (documentada aquí y en docs/arquitectura.md):
    - 0 parámetros fuera del óptimo  -> SALUDABLE
    - 1 parámetro fuera del óptimo   -> EN_RIESGO
    - 2 o más parámetros fuera del óptimo -> CRITICO

Justificación: es una regla simple, predecible y fácil de probar, que no
requiere ponderar la severidad de cada parámetro individualmente (esa es
una posible extensión futura vía OCP: se podría inyectar una estrategia
que pondere temperatura más que luz, por ejemplo, sin tocar EvaluadorPlanta).

Vive en dominio/servicios (y no en infraestructura) porque es una regla de
negocio, no un detalle técnico: no depende de Flask, CSV, ni nada externo.
"""
from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.indice_vitalidad import IndiceVitalidad


class EstrategiaAgregacionPorConteo:
    def calcular(self, estados: dict[str, EstadoParametro]) -> IndiceVitalidad:
        fuera_de_optimo = sum(
            1 for estado in estados.values() if estado != EstadoParametro.OPTIMO
        )

        if fuera_de_optimo == 0:
            return IndiceVitalidad.SALUDABLE
        if fuera_de_optimo == 1:
            return IndiceVitalidad.EN_RIESGO
        return IndiceVitalidad.CRITICO
