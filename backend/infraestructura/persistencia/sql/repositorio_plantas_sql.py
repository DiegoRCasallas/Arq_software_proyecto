from infraestructura.persistencia.sql.modelos import (
    db,
    MedicionModelo,
    PlantaModelo,
    ValorMedicionModelo,
)

class RepositorioPlantasSQL:
    @staticmethod
    def _a_dominio(planta_db):
        from dominio.entidades.planta import Planta

        return Planta(
            id=planta_db.id,
            usuario_id=planta_db.usuario_id,
            especie=planta_db.especie,
            apodo=planta_db.apodo,
            dispositivo_id=planta_db.dispositivo_id,
            token_dispositivo_hash=planta_db.token_dispositivo_hash,
        )

    def obtener_por_dispositivo(self, dispositivo_id: str):
        planta_db = PlantaModelo.query.filter_by(dispositivo_id=dispositivo_id).first()
        return self._a_dominio(planta_db) if planta_db else None

    def obtener(self, planta_id: int):
        planta_db = PlantaModelo.query.get(planta_id)
        return self._a_dominio(planta_db) if planta_db else None

    def listar_por_usuario(self, usuario_id: int):
        plantas = PlantaModelo.query.filter_by(usuario_id=usuario_id).order_by(PlantaModelo.id).all()
        return [self._a_dominio(planta) for planta in plantas]

    def guardar(self, planta):
        planta_db = PlantaModelo(
            usuario_id=planta.usuario_id,
            especie=planta.especie,
            apodo=planta.apodo,
            dispositivo_id=planta.dispositivo_id,
            token_dispositivo_hash=planta.token_dispositivo_hash,
        )
        db.session.add(planta_db)
        db.session.commit()
        planta.id = planta_db.id
        return planta

    def eliminar(self, planta_id: int) -> bool:
        planta_db = db.session.get(PlantaModelo, planta_id)
        if planta_db is None:
            return False

        mediciones = db.select(MedicionModelo.id).where(MedicionModelo.planta_id == planta_id)
        db.session.execute(
            db.delete(ValorMedicionModelo).where(
                ValorMedicionModelo.medicion_id.in_(mediciones)
            )
        )
        db.session.execute(
            db.delete(MedicionModelo).where(MedicionModelo.planta_id == planta_id)
        )
        db.session.delete(planta_db)
        db.session.commit()
        return True