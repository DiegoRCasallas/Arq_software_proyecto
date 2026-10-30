from typing import Protocol

class ServicioTokens(Protocol):
    def generar_token(self, usuario_id: int) -> str:
        ...

    def validar_token(self, token: str) -> dict:
        ...