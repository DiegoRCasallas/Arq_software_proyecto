import csv
import os
from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.valores.rango_referencia import RangoReferencia

class TablaReferenciaCSV:
    def __init__(self, ruta_csv: str = 'infraestructura/persistencia/csv/rangos_especie.csv'):
        self.ruta_csv = ruta_csv

    def obtener_perfil(self, especie: str) -> PerfilEspecie:
        if not os.path.exists(self.ruta_csv):
            return None

        rangos_dominio = {}
        with open(self.ruta_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for fila in reader:
                if fila['especie'] == especie:
                    rangos_dominio[fila['parametro']] = RangoReferencia(
                        parametro=fila['parametro'],
                        minimo=float(fila['minimo']),
                        optimo_min=float(fila['optimo_min']),
                        optimo_max=float(fila['optimo_max']),
                        maximo=float(fila['maximo'])
                    )
        
        if not rangos_dominio:
            return None
            
        return PerfilEspecie(nombre_especie=especie, rangos=rangos_dominio)