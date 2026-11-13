from typing import List

from dominio.entidades.perfil_especie import PerfilEspecie
from dominio.excepciones.errores_dominio import EspecieNoEncontrada
from dominio.valores.rango_referencia import RangoReferencia
from infraestructura.persistencia.sql.modelos import EspecieModelo, db


class TablaReferenciaSQL:
    """Adaptador de salida del puerto TablaReferencia respaldado por la base de datos."""

    def obtener_perfil(self, especie: str) -> PerfilEspecie:
        nombre_limpio = especie.strip() if especie else ""
        especie_db = db.session.get(EspecieModelo, nombre_limpio)
        if especie_db is None and nombre_limpio:
            especie_db = db.session.scalar(
                db.select(EspecieModelo).where(
                    db.func.lower(EspecieModelo.nombre) == nombre_limpio.lower()
                )
            )
        if especie_db is None:
            raise EspecieNoEncontrada(especie)
        return self._a_perfil(especie_db)

    def listar_especies(self) -> List[PerfilEspecie]:
        consulta = db.select(EspecieModelo).order_by(EspecieModelo.nombre)
        return [self._a_perfil(e) for e in db.session.scalars(consulta)]

    @staticmethod
    def _a_perfil(especie_db: EspecieModelo) -> PerfilEspecie:
        # Mapeamos los rangos de la infraestructura al dominio
        rangos = {
            r.parametro: RangoReferencia(
                parametro=r.parametro,
                minimo=r.minimo,
                optimo_min=r.optimo_min,
                optimo_max=r.optimo_max,
                maximo=r.maximo,
            )
            for r in especie_db.rangos
        }
        return PerfilEspecie(nombre_especie=especie_db.nombre, rangos=rangos)
