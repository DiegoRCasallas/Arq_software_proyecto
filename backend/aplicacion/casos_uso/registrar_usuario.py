from dominio.entidades.usuario import Usuario
from dominio.excepciones.errores_dominio import ErrorDominio

class RegistrarUsuario:
    def __init__(self, repo_usuarios, hasher_contrasenas):
        self.repo_usuarios = repo_usuarios
        self.hasher = hasher_contrasenas

    def ejecutar(self, nombre: str, email: str, contrasena: str) -> Usuario:
        if self.repo_usuarios.obtener_por_email(email):
            raise ErrorDominio("El email ya está registrado")
            
        hash_pass = self.hasher.hashear(contrasena)
        nuevo_usuario = Usuario(id=None, nombre=nombre, email=email, password_hash=hash_pass)
        
        return self.repo_usuarios.guardar(nuevo_usuario)