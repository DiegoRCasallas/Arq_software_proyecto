from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.valores.rango_referencia import RangoReferencia
from infraestructura.persistencia.sql.modelos import EspecieModelo

class TablaReferenciaSQL:
    def obtener_perfil(self, especie: str) -> PerfilEspecie:
        # 1. Buscamos la especie en la base de datos
        especie_db = EspecieModelo.query.get(especie)
        if not especie_db:
            return None
        
        # 2. Mapeamos los rangos de la infraestructura al dominio
        rangos_dominio = {}
        for r in especie_db.rangos:
            rangos_dominio[r.parametro] = RangoReferencia(
                parametro=r.parametro,
                minimo=r.minimo,
                optimo_min=r.optimo_min,
                optimo_max=r.optimo_max,
                maximo=r.maximo
            )
            
        return PerfilEspecie(nombre_especie=especie_db.nombre, rangos=rangos_dominio)