"""
VincularDispositivo: caso de uso que asocia un dispositivo físico (ESP32)
a una planta existente del usuario.

El ESP32 muestra un QR en su pantalla con sus propias credenciales:
  { "id": hash(MAC), "token": "token_plano_pregrabado" }

El usuario escanea el QR con la app. El frontend envía esos datos a este
caso de uso, que los valida y los persiste (el token se guarda hasheado).

Pasos:
1. Verificar que la planta existe y pertenece al usuario autenticado.
2. Si el dispositivo ya está en otra planta:
   - Si pertenece a otro usuario, rechazar con ErrorDominio.
   - Si pertenece al mismo usuario, desvincularlo primero de la planta anterior.
3. Hashear el token recibido del QR.
4. Persistir dispositivo_id y token_hash en la planta destino.
"""
from dominio.excepciones.errores_dominio import ErrorDominio
from dominio.puertos.hasher_contrasenas import HasherContrasenas
from dominio.puertos.repositorio_plantas import RepositorioPlantas


class VincularDispositivo:
    def __init__(
        self,
        repo_plantas: RepositorioPlantas,
        hasher: HasherContrasenas,
    ):
        self.repo_plantas = repo_plantas
        self.hasher = hasher

    def ejecutar(
        self,
        usuario_id: int,
        planta_id: int,
        dispositivo_id: str,
        token_plano: str,
    ) -> dict:
        """
        dispositivo_id: hash de la MAC del ESP32 (leído del QR).
        token_plano:    token del ESP32 en texto plano (leído del QR).

        Retorna {'dispositivo_id': str, 'reasignado_desde_planta_id': int | None}.
        """
        planta = self.repo_plantas.obtener(planta_id)
        if planta is None or not planta.pertenece_a(usuario_id):
            raise ErrorDominio("Planta no encontrada")

        planta_anterior_id = None
        planta_existente = self.repo_plantas.obtener_por_dispositivo(dispositivo_id)

        if planta_existente is not None and planta_existente.id != planta_id:
            if not planta_existente.pertenece_a(usuario_id):
                raise ErrorDominio("Este dispositivo ya está vinculado a otra planta")

            # Desvincular primero de la planta anterior del mismo usuario
            # para evitar conflicto con la restricción UNIQUE de dispositivo_id en BD.
            self.repo_plantas.actualizar_dispositivo(planta_existente.id, None, None)
            planta_anterior_id = planta_existente.id

        token_hash = self.hasher.hashear(token_plano)
        self.repo_plantas.actualizar_dispositivo(planta_id, dispositivo_id, token_hash)

        return {
            "dispositivo_id": dispositivo_id,
            "reasignado_desde_planta_id": planta_anterior_id,
        }
