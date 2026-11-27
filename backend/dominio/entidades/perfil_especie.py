"""
PerfilEspecie: agrupa los rangos de referencia de cada parámetro medible
para una especie determinada (temperatura, humedad, luz, etc.).

Además de describir a la especie, conoce qué mediciones son aceptables para
ella (validar_medicion): es una regla de negocio y por eso vive en el dominio.
"""
from typing import Dict

from dominio.entidades.medicion import Medicion
from dominio.excepciones.errores_dominio import (
    ParametroDesconocido,
    ValorFueraDeRangoFisico,
)
from dominio.valores.rango_referencia import RangoReferencia


class PerfilEspecie:
    def __init__(self, nombre_especie: str, rangos: Dict[str, RangoReferencia]):
        self.nombre_especie = nombre_especie
        self.rangos = rangos

    def validar_medicion(self, medicion: Medicion) -> None:
        """
        Verifica que la medición sea aceptable para esta especie. No la
        evalúa (BAJO/OPTIMO/ALTO): solo decide si se puede aceptar y guardar.

        Reglas, en este orden:
          1. Todo parámetro enviado debe existir en el perfil.
             -> ParametroDesconocido
          2. Cada valor enviado debe ser físicamente posible, es decir, estar dentro
             de [minimo, maximo] de su rango. -> ValorFueraDeRangoFisico

        Lanza la primera excepción de dominio que encuentre.
        """
        for parametro in medicion.valores:
            if parametro not in self.rangos:
                raise ParametroDesconocido(parametro, self.nombre_especie)

        for parametro, valor in medicion.valores.items():
            rango = self.rangos[parametro]
            if not rango.validar_fisicamente(valor):
                raise ValorFueraDeRangoFisico(parametro, valor, rango.minimo, rango.maximo)
