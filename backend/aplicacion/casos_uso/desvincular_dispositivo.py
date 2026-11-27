"""
DesvincularDispositivo: caso de uso que rompe la asociación entre una
planta y su dispositivo ESP32.

El dispositivo deja de poder enviar mediciones inmediatamente, ya que el
token_dispositivo_hash queda como NULL y la autenticación fallará.
"""
from dominio.excepciones.errores_dominio import ErrorDominio
from dominio.puertos.repositorio_plantas import RepositorioPlantas


class DesvincularDispositivo:
    def __init__(self, repo_plantas: RepositorioPlantas):
        self.repo_plantas = repo_plantas

    def ejecutar(self, usuario_id: int, planta_id: int) -> None:
        planta = self.repo_plantas.obtener(planta_id)
        if planta is None or not planta.pertenece_a(usuario_id):
            raise ErrorDominio("Planta no encontrada")

        if not planta.dispositivo_id:
            raise ErrorDominio("Esta planta no tiene un dispositivo vinculado")

        self.repo_plantas.actualizar_dispositivo(planta_id, None, None)

