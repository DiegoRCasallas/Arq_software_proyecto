from datetime import datetime

from sqlalchemy import update

from infraestructura.persistencia.sql.modelos import (
    db,
    SesionVinculacionModelo,
)


class RepositorioSesionesVinculacionSQL:
    @staticmethod
    def _a_dominio(modelo):
        from dominio.entidades.sesion_vinculacion import SesionVinculacion

        return SesionVinculacion(
            id=modelo.id,
            dispositivo_id=modelo.dispositivo_id,
            usuario_id=modelo.usuario_id,
            planta_id=modelo.planta_id,
            codigo_hash=modelo.codigo_hash,
            token_dispositivo_hash=modelo.token_dispositivo_hash,
            expira_en=modelo.expira_en,
            completada_en=modelo.completada_en,
        )

    def crear(self, sesion) -> None:
        modelo = db.session.scalar(
            db.select(SesionVinculacionModelo).where(
                SesionVinculacionModelo.dispositivo_id == sesion.dispositivo_id
            )
        )
        if modelo is None:
            modelo = SesionVinculacionModelo(
                dispositivo_id=sesion.dispositivo_id
            )
            db.session.add(modelo)

        modelo.id = sesion.id
        modelo.usuario_id = sesion.usuario_id
        modelo.planta_id = sesion.planta_id
        modelo.codigo_hash = sesion.codigo_hash
        modelo.token_dispositivo_hash = sesion.token_dispositivo_hash
        modelo.expira_en = sesion.expira_en
        modelo.completada_en = sesion.completada_en
        db.session.commit()

    def obtener_por_dispositivo(self, dispositivo_id: str):
        modelo = db.session.scalar(
            db.select(SesionVinculacionModelo).where(
                SesionVinculacionModelo.dispositivo_id == dispositivo_id
            )
        )
        return self._a_dominio(modelo) if modelo else None

    def obtener(self, sesion_id: str):
        modelo = db.session.get(SesionVinculacionModelo, sesion_id)
        return self._a_dominio(modelo) if modelo else None

    def obtener_por_codigo(self, dispositivo_id: str, codigo_hash: str):
        modelo = db.session.scalar(
            db.select(SesionVinculacionModelo)
            .where(
                SesionVinculacionModelo.dispositivo_id == dispositivo_id,
                SesionVinculacionModelo.codigo_hash == codigo_hash,
            )
            .order_by(SesionVinculacionModelo.expira_en.desc())
        )
        return self._a_dominio(modelo) if modelo else None

    def reclamar(self, sesion_id: str, usuario_id: int, planta_id: int) -> bool:
        ahora = datetime.utcnow()
        resultado = db.session.execute(
            update(SesionVinculacionModelo)
            .where(
                SesionVinculacionModelo.id == sesion_id,
                SesionVinculacionModelo.usuario_id.is_(None),
                SesionVinculacionModelo.completada_en.is_(None),
                SesionVinculacionModelo.expira_en > ahora,
            )
            .values(usuario_id=usuario_id, planta_id=planta_id)
        )
        if resultado.rowcount:
            db.session.commit()
            return True

        modelo = db.session.get(SesionVinculacionModelo, sesion_id)
        if (
            modelo is not None
            and modelo.usuario_id == usuario_id
            and modelo.planta_id == planta_id
            and modelo.completada_en is None
            and modelo.expira_en > ahora
        ):
            return True
        db.session.rollback()
        return False

    def marcar_completada(self, sesion_id: str, fecha) -> None:
        modelo = db.session.get(SesionVinculacionModelo, sesion_id)
        if modelo is None:
            raise LookupError("La sesión de vinculación ya no existe")
        modelo.completada_en = fecha
        db.session.commit()

    def cancelar(self, sesion_id: str, fecha) -> None:
        modelo = db.session.get(SesionVinculacionModelo, sesion_id)
        if modelo is None or modelo.completada_en is not None:
            return
        modelo.expira_en = fecha
        db.session.commit()

