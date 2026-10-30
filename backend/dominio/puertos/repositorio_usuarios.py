from typing import Protocol, Optional
from dominio.entidades.usuario import Usuario

class RepositorioUsuarios(Protocol):
    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        ...
        
    def guardar(self, usuario: Usuario) -> Usuario:
        ...