from dominio.excepciones.errores_dominio import ErrorDominio

class IniciarSesion:
    def __init__(self, repo_usuarios, hasher_contrasenas, servicio_tokens):
        self.repo_usuarios = repo_usuarios
        self.hasher = hasher_contrasenas
        self.servicio_tokens = servicio_tokens

    def ejecutar(self, email: str, contrasena: str) -> str:
        usuario = self.repo_usuarios.obtener_por_email(email)
        if not usuario:
            raise ErrorDominio("Credenciales inválidas")
            
        if not self.hasher.verificar(contrasena, usuario.password_hash):
            raise ErrorDominio("Credenciales inválidas")
            
        return self.servicio_tokens.generar_token(usuario.id)