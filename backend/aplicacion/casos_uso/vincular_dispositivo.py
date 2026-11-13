"""
VincularDispositivo: caso de uso que asocia un dispositivo físico (ESP32)
a una planta existente del usuario.

El ESP32 muestra un QR en su pantalla con sus propias credenciales:
  { "id": hash(MAC), "token": "token_plano_pregrabado" }

El usuario escanea el QR con la app. El frontend envía esos datos a este
caso de uso, que los valida y los persiste (el token se guarda hasheado).

Pasos:
  1. Verificar que la planta existe y pertenece al usuario autenticado.
  2. Verificar que el dispositivo_id no esté ya vinculado a otra planta.
  3. Hashear el token recibido del QR.
  4. Persistir dispositivo_id y token_hash en la planta.
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

    def ejecutar(self, usuario_id: int, planta_id: int, dispositivo_id: str, token_plano: str) -> dict:
        """
        dispositivo_id: hash de la MAC del ESP32 (leído del QR).
        token_plano:    token del ESP32 en texto plano (leído del QR).
        
        Retorna {'dispositivo_id': str} confirmando la vinculación.
        """
        planta = self.repo_plantas.obtener(planta_id)
        if planta is None or not planta.pertenece_a(usuario_id):
            raise ErrorDominio("Planta no encontrada")

        # Verificar que ese dispositivo_id no esté ya asignado a otra planta
        planta_existente = self.repo_plantas.obtener_por_dispositivo(dispositivo_id)
        if planta_existente is not None and planta_existente.id != planta_id:
            raise ErrorDominio("Este dispositivo ya está vinculado a otra planta")

        token_hash = self.hasher.hashear(token_plano)
        self.repo_plantas.actualizar_dispositivo(planta_id, dispositivo_id, token_hash)

        return {"dispositivo_id": dispositivo_id}

