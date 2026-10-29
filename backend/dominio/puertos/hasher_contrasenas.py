from typing import Protocol

class HasherContrasenas(Protocol):
    def hashear(self, texto: str) -> str:
        ...

    def verificar(self, texto: str, hash_texto: str) -> bool:
        ...