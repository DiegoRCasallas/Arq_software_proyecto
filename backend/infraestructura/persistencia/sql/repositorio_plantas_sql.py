from dominio.valores.estado_animo import EstadoAnimo
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
            # --- NUEVO: reconstrucción de gamificación ---
            experiencia=planta_db.experiencia,
            nivel=planta_db.nivel,
            estado_animo=EstadoAnimo(planta_db.estado_animo),
            xp_minijuego_hoy=planta_db.xp_minijuego_hoy,
            fecha_ultimo_minijuego=planta_db.fecha_ultimo_minijuego,
        )

    def obtener_por_dispositivo(self, dispositivo_id: str):
        planta_db = db.session.scalar(
            db.select(PlantaModelo).where(PlantaModelo.dispositivo_id == dispositivo_id)
        )
        return self._a_dominio(planta_db) if planta_db else None

    def obtener(self, planta_id: int):
        planta_db = db.session.get(PlantaModelo, planta_id)
        return self._a_dominio(planta_db) if planta_db else None

    def listar_por_usuario(self, usuario_id: int):
        plantas = db.session.scalars(
            db.select(PlantaModelo).where(PlantaModelo.usuario_id == usuario_id).order_by(PlantaModelo.id)
        ).all()
        return [self._a_dominio(planta) for planta in plantas]

    def guardar(self, planta):
        planta_db = PlantaModelo(
            usuario_id=planta.usuario_id,
            especie=planta.especie,
            apodo=planta.apodo,
            dispositivo_id=planta.dispositivo_id,
            token_dispositivo_hash=planta.token_dispositivo_hash,
            # --- NUEVO: persistir valores iniciales de gamificación ---
            experiencia=planta.experiencia,
            nivel=planta.nivel,
            estado_animo=planta.estado_animo.value,
            xp_minijuego_hoy=planta.xp_minijuego_hoy,
            fecha_ultimo_minijuego=planta.fecha_ultimo_minijuego,
        )
        db.session.add(planta_db)
        db.session.commit()
        planta.id = planta_db.id
        return planta

    def actualizar(self, planta) -> None:
        """Persiste cambios de estado de la entidad Planta (experiencia, nivel, ánimo)."""
        planta_db = db.session.get(PlantaModelo, planta.id)
        if planta_db is None:
            return
        planta_db.experiencia = planta.experiencia
        planta_db.nivel = planta.nivel
        planta_db.estado_animo = planta.estado_animo.value
        planta_db.xp_minijuego_hoy = planta.xp_minijuego_hoy
        planta_db.fecha_ultimo_minijuego = planta.fecha_ultimo_minijuego
        db.session.commit()

    def actualizar_dispositivo(self, planta_id: int, dispositivo_id, token_hash) -> None:
        """Vincula o desvincula (None) un ESP32 de la planta."""
        planta_db = db.session.get(PlantaModelo, planta_id)
        if planta_db is None:
            return
        planta_db.dispositivo_id = dispositivo_id
        planta_db.token_dispositivo_hash = token_hash
        db.session.commit()

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
