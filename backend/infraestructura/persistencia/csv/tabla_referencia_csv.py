"""
TablaReferenciaCSV: adaptador de salida del puerto TablaReferencia que lee
los perfiles de especies desde un archivo CSV.

Formato (una fila por especie, columnas por parámetro):

    especie,humedad_min,humedad_optimo_min,humedad_optimo_max,humedad_max,luz_min,...,fuente

Los parámetros se detectan a partir de las columnas que terminan en
"_optimo_min", así que agregar un parámetro nuevo (p. ej. ph_min, ph_optimo_min,
ph_optimo_max, ph_max) no requiere cambiar este código.

La búsqueda de especie ignora mayúsculas y espacios ("  ALBAHACA " == "albahaca").
"""
import csv
from pathlib import Path
from typing import Dict, List, Optional, Union

from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.excepciones.errores_dominio import EspecieNoEncontrada
from dominio.valores.rango_referencia import RangoReferencia

# Ruta relativa a ESTE archivo (no al directorio de trabajo): funciona igual
# se ejecute la app desde backend/, desde la raíz o bajo gunicorn.
RUTA_POR_DEFECTO = Path(__file__).resolve().parent.parent / "especies.csv"

_SUFIJO_OPTIMO_MIN = "_optimo_min"


class TablaReferenciaCSV:
    def __init__(self, ruta_csv: Union[str, Path] = RUTA_POR_DEFECTO):
        self._ruta = Path(ruta_csv)
        self._perfiles: Optional[Dict[str, PerfilEspecie]] = None

    def obtener_perfil(self, especie: str) -> PerfilEspecie:
        perfil = self._cargar().get(especie.strip().lower())
        if perfil is None:
            raise EspecieNoEncontrada(especie)
        return perfil

    def listar_especies(self) -> List[PerfilEspecie]:
        return list(self._cargar().values())

    def _cargar(self) -> Dict[str, PerfilEspecie]:
        if self._perfiles is None:
            self._perfiles = self._leer()
        return self._perfiles

    def _leer(self) -> Dict[str, PerfilEspecie]:
        perfiles: Dict[str, PerfilEspecie] = {}
        with open(self._ruta, mode="r", encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            parametros = [
                columna[: -len(_SUFIJO_OPTIMO_MIN)]
                for columna in (lector.fieldnames or [])
                if columna.endswith(_SUFIJO_OPTIMO_MIN)
            ]
            for fila in lector:
                nombre = fila["especie"].strip()
                rangos = {
                    p: RangoReferencia(
                        parametro=p,
                        minimo=float(fila[f"{p}_min"]),
                        optimo_min=float(fila[f"{p}_optimo_min"]),
                        optimo_max=float(fila[f"{p}_optimo_max"]),
                        maximo=float(fila[f"{p}_max"]),
                    )
                    for p in parametros
                }
                perfiles[nombre.lower()] = PerfilEspecie(nombre_especie=nombre, rangos=rangos)
        return perfiles
