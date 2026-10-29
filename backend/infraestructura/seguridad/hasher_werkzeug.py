from werkzeug.security import generate_password_hash, check_password_hash

class HasherWerkzeug:
    """
    Adaptador de salida para manejar hashes de contraseñas y tokens.
    Implementa la interfaz HasherContrasenas del dominio.
    """
    def hashear(self, texto: str) -> str:
        return generate_password_hash(texto)

    def verificar(self, texto: str, hash_texto: str) -> bool:
        return check_password_hash(hash_texto, texto)