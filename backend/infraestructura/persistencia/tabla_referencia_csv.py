"""
TablaReferenciaCSV: implementación concreta del puerto TablaReferencia
(dominio/puertos/tabla_referencia.py) que lee los perfiles de especies
desde un archivo CSV.

RA5 / RA4: esta es la ÚNICA clase del proyecto que sabe que existe un
archivo CSV. El dominio (EvaluadorPlanta, casos de uso) solo conoce la
interfaz TablaReferencia; si mañana se reemplaza este archivo por una
implementación con base de datos (p. ej. TablaReferenciaBaseDatos), basta
con crear esa nueva clase e inyectarla donde hoy se inyecta esta —
cero cambios en el dominio.

LSP: cualquier otra implementación de TablaReferencia (por ejemplo, una
futura TablaReferenciaBaseDatos) debe poder sustituir a esta sin que
el código que la usa note la diferencia, siempre que respete el mismo
contrato (obtener_perfil, listar_especies).
"""
import csv
from pathlib import Path

from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.valores.rango_referencia import RangoReferencia
from dominio.excepciones.errores_dominio import EspecieNoEncontrada


class TablaReferenciaCSV:
    def __init__(self, ruta_csv: str | Path):
        self._ruta_csv = Path(ruta_csv)
        self._perfiles: dict[str, PerfilEspecie] = {}
        self._cargar()

    def _cargar(self) -> None:
        with open(self._ruta_csv, encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)
            for fila in lector:
                perfil = self._fila_a_perfil(fila)
                self._perfiles[perfil.nombre_especie.lower()] = perfil

    @staticmethod
    def _fila_a_perfil(fila: dict) -> PerfilEspecie:
        nombre_especie = fila["especie"].strip()

        rango_humedad = RangoReferencia(
            nombre_parametro="humedad",
            minimo=float(fila["humedad_min"]),
            optimo_min=float(fila["humedad_optimo_min"]),
            optimo_max=float(fila["humedad_optimo_max"]),
            maximo=float(fila["humedad_max"]),
        )
        rango_luz = RangoReferencia(
            nombre_parametro="luz",
            minimo=float(fila["luz_min"]),
            optimo_min=float(fila["luz_optimo_min"]),
            optimo_max=float(fila["luz_optimo_max"]),
            maximo=float(fila["luz_max"]),
        )
        rango_temperatura = RangoReferencia(
            nombre_parametro="temperatura",
            minimo=float(fila["temperatura_min"]),
            optimo_min=float(fila["temperatura_optimo_min"]),
            optimo_max=float(fila["temperatura_optimo_max"]),
            maximo=float(fila["temperatura_max"]),
        )

        return PerfilEspecie(
            nombre_especie=nombre_especie,
            rango_humedad=rango_humedad,
            rango_luz=rango_luz,
            rango_temperatura=rango_temperatura,
        )

    def obtener_perfil(self, especie: str) -> PerfilEspecie:
        perfil = self._perfiles.get(especie.strip().lower())
        if perfil is None:
            raise EspecieNoEncontrada(especie)
        return perfil

    def listar_especies(self) -> list[PerfilEspecie]:
        return list(self._perfiles.values())
