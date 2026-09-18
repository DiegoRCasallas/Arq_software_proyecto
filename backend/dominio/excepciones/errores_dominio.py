"""
Excepciones del dominio.

Importante (RA6): estas excepciones NO conocen HTTP ni códigos de estado.
Es responsabilidad de la capa de presentación traducir cada una de estas
excepciones a un código HTTP y a un cuerpo de error uniforme (RF6).
"""


class ErrorDominio(Exception):
    """Clase base de todas las excepciones del dominio."""


class EspecieNoEncontrada(ErrorDominio):
    """Se solicitó una especie que no existe en la tabla de referencia."""

    def __init__(self, especie: str):
        self.especie = especie
        super().__init__(f"La especie '{especie}' no está soportada.")


class ParametroAusente(ErrorDominio):
    """Falta un parámetro obligatorio en la medición (humedad, luz o temperatura)."""

    def __init__(self, nombre_parametro: str):
        self.nombre_parametro = nombre_parametro
        super().__init__(f"Falta el parámetro obligatorio '{nombre_parametro}'.")


class ValorNoNumerico(ErrorDominio):
    """Un parámetro recibido no es un valor numérico válido."""

    def __init__(self, nombre_parametro: str, valor_recibido):
        self.nombre_parametro = nombre_parametro
        self.valor_recibido = valor_recibido
        super().__init__(
            f"El parámetro '{nombre_parametro}' debe ser numérico "
            f"(se recibió: {valor_recibido!r})."
        )


class ValorFueraDeRangoFisico(ErrorDominio):
    """
    Un valor es físicamente imposible para ese parámetro
    (distinto de estar fuera del rango óptimo de la especie).
    """

    def __init__(self, nombre_parametro: str, valor: float, minimo_fisico: float, maximo_fisico: float):
        self.nombre_parametro = nombre_parametro
        self.valor = valor
        self.minimo_fisico = minimo_fisico
        self.maximo_fisico = maximo_fisico
        super().__init__(
            f"El valor de '{nombre_parametro}' ({valor}) está fuera del rango "
            f"físicamente posible [{minimo_fisico}, {maximo_fisico}]."
        )
