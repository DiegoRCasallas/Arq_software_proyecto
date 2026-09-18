"""
Traduce excepciones del dominio a respuestas HTTP uniformes (RF6).

Este es el único lugar de la aplicación que conoce la relación entre
una excepción de dominio y un código HTTP. Los controladores solo
llaman a `manejar_error_dominio(excepcion)` dentro de un except.

Estructura de error uniforme:
{
    "error": "<CODIGO>",
    "mensaje": "<texto legible>"
}
"""
from dominio.excepciones.errores_dominio import (
    EspecieNoEncontrada,
    ParametroAusente,
    ValorNoNumerico,
    ValorFueraDeRangoFisico,
    ErrorDominio,
)

_MAPEO_CODIGO_HTTP = {
    EspecieNoEncontrada: ("ESPECIE_NO_ENCONTRADA", 404),
    ParametroAusente: ("PARAMETRO_AUSENTE", 400),
    ValorNoNumerico: ("VALOR_NO_NUMERICO", 400),
    ValorFueraDeRangoFisico: ("VALOR_FUERA_DE_RANGO_FISICO", 400),
}


def manejar_error_dominio(excepcion: ErrorDominio) -> tuple[dict, int]:
    codigo, status_http = _MAPEO_CODIGO_HTTP.get(
        type(excepcion), ("ERROR_INTERNO", 500)
    )
    cuerpo = {"error": codigo, "mensaje": str(excepcion)}
    return cuerpo, status_http
