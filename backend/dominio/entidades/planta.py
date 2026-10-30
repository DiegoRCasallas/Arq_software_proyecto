from typing import Optional


class Planta:
    def __init__(
        self,
        id: Optional[int],
        usuario_id: int,
        especie: str,
        apodo: Optional[str] = None,
        dispositivo_id: Optional[str] = None,
        token_dispositivo_hash: Optional[str] = None,
    ):
        self.id = id
        self.usuario_id = usuario_id
        self.especie = especie
        self.apodo = apodo
        self.dispositivo_id = dispositivo_id
        self.token_dispositivo_hash = token_dispositivo_hash

    def pertenece_a(self, usuario_id: int) -> bool:
        """Regla de negocio: Verifica si la planta pertenece a un usuario específico"""
        return self.usuario_id == usuario_id