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

Una ErrorDominio sin mapeo específico se trata como error de negocio genérico
(400), nunca como 500: un 500 significa "falló el servidor", no "la petición
no es aceptable".
"""
from dominio.excepciones.errores_dominio import (
    DispositivoNoAutorizado,
    ErrorDominio,
    EspecieNoEncontrada,
    ParametroAusente,
    ParametroDesconocido,
    ValorFueraDeRangoFisico,
    ValorNoNumerico,
)

_MAPEO_CODIGO_HTTP = (
    (DispositivoNoAutorizado, "DISPOSITIVO_NO_AUTORIZADO", 401),
    (EspecieNoEncontrada, "ESPECIE_NO_ENCONTRADA", 404),
    (ParametroAusente, "PARAMETRO_AUSENTE", 400),
    (ParametroDesconocido, "PARAMETRO_DESCONOCIDO", 400),
    (ValorNoNumerico, "VALOR_NO_NUMERICO", 400),
    (ValorFueraDeRangoFisico, "VALOR_FUERA_DE_RANGO_FISICO", 400),
)


def manejar_error_dominio(excepcion: ErrorDominio) -> tuple[dict, int]:
    for tipo, codigo, status_http in _MAPEO_CODIGO_HTTP:
        if isinstance(excepcion, tipo):
            return {"error": codigo, "mensaje": str(excepcion)}, status_http
    return {"error": "ERROR_DE_NEGOCIO", "mensaje": str(excepcion)}, 400
