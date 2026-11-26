import hashlib
import secrets
from datetime import datetime, timedelta

from dominio.entidades.sesion_vinculacion import SesionVinculacion
from dominio.excepciones.errores_dominio import ErrorDominio


class VinculacionQR:
    DURACION_SESION = timedelta(minutes=5)

    def __init__(
        self,
        repo_plantas,
        repo_sesiones,
        hasher,
        caso_vincular,
    ):
        self.repo_plantas = repo_plantas
        self.repo_sesiones = repo_sesiones
        self.hasher = hasher
        self.caso_vincular = caso_vincular

    @staticmethod
    def _hash_codigo(codigo: str) -> str:
        return hashlib.sha256(codigo.encode("utf-8")).hexdigest()

    def _dispositivo_esta_vinculado(
        self, dispositivo_id: str, token_dispositivo: str
    ) -> bool:
        planta = self.repo_plantas.obtener_por_dispositivo(dispositivo_id)
        return bool(
            planta
            and planta.token_dispositivo_hash
            and self.hasher.verificar(
                token_dispositivo, planta.token_dispositivo_hash
            )
        )

    def preparar(
        self, dispositivo_id: str, codigo: str, token_dispositivo: str
    ) -> dict:
        ahora = datetime.utcnow()
        codigo_hash = self._hash_codigo(codigo)
        anterior = self.repo_sesiones.obtener_por_dispositivo(dispositivo_id)

        if anterior is not None:
            if not self.hasher.verificar(
                token_dispositivo, anterior.token_dispositivo_hash
            ):
                raise ErrorDominio("Credencial de dispositivo inválida")

            if anterior.codigo_hash == codigo_hash:
                if anterior.completada_en is not None:
                    if self._dispositivo_esta_vinculado(
                        dispositivo_id, token_dispositivo
                    ):
                        return {"estado": "completada"}
                    raise ErrorDominio("Código de vinculación inválido o expirado")
                if anterior.expira_en > ahora:
                    estado = "solicitada" if anterior.usuario_id is not None else "preparada"
                    return {"sesion_id": anterior.id, "estado": estado}
                raise ErrorDominio("Código de vinculación inválido o expirado")

            if anterior.completada_en is None and anterior.expira_en > ahora:
                raise ErrorDominio("Ya existe una sesión de vinculación activa")

        sesion = SesionVinculacion(
            id=secrets.token_urlsafe(24),
            dispositivo_id=dispositivo_id,
            usuario_id=None,
            planta_id=None,
            codigo_hash=codigo_hash,
            token_dispositivo_hash=self.hasher.hashear(token_dispositivo),
            expira_en=ahora + self.DURACION_SESION,
        )
        self.repo_sesiones.crear(sesion)
        return {"sesion_id": sesion.id, "estado": "preparada"}

    def solicitar(
        self,
        usuario_id: int,
        planta_id: int,
        dispositivo_id: str,
        codigo: str,
    ) -> dict:
        planta = self.repo_plantas.obtener(planta_id)
        if planta is None or not planta.pertenece_a(usuario_id):
            raise ErrorDominio("Planta no encontrada")

        sesion = self.repo_sesiones.obtener_por_codigo(
            dispositivo_id, self._hash_codigo(codigo)
        )
        if (
            sesion is None
            or sesion.completada_en is not None
            or sesion.expira_en <= datetime.utcnow()
        ):
            raise ErrorDominio("Código de vinculación inválido o expirado")

        if sesion.usuario_id is not None and (
            sesion.usuario_id != usuario_id or sesion.planta_id != planta_id
        ):
            raise ErrorDominio("El código ya tiene una solicitud activa")

        if not self.repo_sesiones.reclamar(sesion.id, usuario_id, planta_id):
            raise ErrorDominio("El código ya tiene una solicitud activa")
        return {"sesion_id": sesion.id, "estado": "pendiente"}

    def consultar(
        self, usuario_id: int, planta_id: int, sesion_id: str
    ) -> dict:
        sesion = self.repo_sesiones.obtener(sesion_id)
        if (
            sesion is None
            or sesion.usuario_id != usuario_id
            or sesion.planta_id != planta_id
        ):
            raise ErrorDominio("Vinculación no encontrada")

        if sesion.completada_en is not None:
            return {"estado": "completada"}
        if sesion.expira_en <= datetime.utcnow():
            return {"estado": "expirada"}
        return {"estado": "pendiente"}

    def cancelar(self, usuario_id: int, planta_id: int, sesion_id: str) -> None:
        sesion = self.repo_sesiones.obtener(sesion_id)
        if (
            sesion is None
            or sesion.usuario_id != usuario_id
            or sesion.planta_id != planta_id
        ):
            raise ErrorDominio("Vinculación no encontrada")
        if sesion.completada_en is not None:
            raise ErrorDominio("La vinculación ya fue completada")
        self.repo_sesiones.cancelar(sesion_id, datetime.utcnow())

    def confirmar(
        self,
        dispositivo_id: str,
        codigo: str,
        token_dispositivo: str,
        aprobar: bool = False,
    ) -> dict:
        sesion = self.repo_sesiones.obtener_por_codigo(
            dispositivo_id, self._hash_codigo(codigo)
        )
        if sesion is None:
            return {"estado": "esperando"}

        if not self.hasher.verificar(
            token_dispositivo, sesion.token_dispositivo_hash
        ):
            raise ErrorDominio("Credencial de dispositivo inválida")

        if sesion.completada_en is not None:
            if self._dispositivo_esta_vinculado(dispositivo_id, token_dispositivo):
                return {"estado": "completada"}
            raise ErrorDominio("Código de vinculación inválido o expirado")

        if sesion.expira_en <= datetime.utcnow():
            raise ErrorDominio("Código de vinculación inválido o expirado")
        if sesion.usuario_id is None or sesion.planta_id is None:
            return {"estado": "esperando"}
        if not aprobar:
            return {"estado": "solicitada"}

        try:
            self.caso_vincular.ejecutar(
                usuario_id=sesion.usuario_id,
                planta_id=sesion.planta_id,
                dispositivo_id=dispositivo_id,
                token_plano=token_dispositivo,
            )
        except ErrorDominio:
            self.repo_sesiones.cancelar(sesion.id, datetime.utcnow())
            raise
        self.repo_sesiones.marcar_completada(sesion.id, datetime.utcnow())
        return {"estado": "completada"}
