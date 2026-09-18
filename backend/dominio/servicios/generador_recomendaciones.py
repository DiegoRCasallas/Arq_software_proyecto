"""
GeneradorRecomendaciones: produce texto legible a partir de los estados
de los parámetros (RF4).

Se separa de EvaluadorPlanta por SRP: la razón de cambio de este módulo
es "cómo se redacta una recomendación", que es independiente de "cómo se
orquesta el diagnóstico completo". Si mañana las recomendaciones vienen
de una plantilla distinta, o se traducen a otro idioma, solo se toca
este archivo.
"""
from dominio.valores.estado_parametro import EstadoParametro

_MENSAJES: dict[str, dict[EstadoParametro, str]] = {
    "humedad": {
        EstadoParametro.BAJO: "Se recomienda aumentar la humedad del sustrato (regar la planta).",
        EstadoParametro.ALTO: "Se recomienda reducir el riego para evitar exceso de humedad.",
    },
    "luz": {
        EstadoParametro.BAJO: "Se recomienda ubicar la planta en un lugar con más luz.",
        EstadoParametro.ALTO: "Se recomienda alejar la planta de la luz directa o darle sombra parcial.",
    },
    "temperatura": {
        EstadoParametro.BAJO: "Se recomienda trasladar la planta a un ambiente más cálido.",
        EstadoParametro.ALTO: "Se recomienda proteger la planta del calor excesivo o ventilar el espacio.",
    },
}


class GeneradorRecomendaciones:
    def generar(self, estados: dict[str, EstadoParametro]) -> list[str]:
        recomendaciones = []
        for nombre_parametro, estado in estados.items():
            if estado == EstadoParametro.OPTIMO:
                continue
            mensaje = _MENSAJES.get(nombre_parametro, {}).get(estado)
            if mensaje:
                recomendaciones.append(mensaje)
        return recomendaciones
