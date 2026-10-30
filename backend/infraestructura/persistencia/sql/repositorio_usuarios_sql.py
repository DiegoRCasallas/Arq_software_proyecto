from dominio.entidades.usuario import Usuario
from infraestructura.persistencia.sql.modelos import db, UsuarioModelo

class RepositorioUsuariosSQL:
    def obtener_por_email(self, email: str) -> Usuario:
        usuario_db = UsuarioModelo.query.filter_by(email=email).first()
        if not usuario_db:
            return None
            
        return Usuario(
            id=usuario_db.id,
            nombre=usuario_db.nombre,
            email=usuario_db.email,
            password_hash=usuario_db.password_hash
        )

    def guardar(self, usuario: Usuario) -> Usuario:
        nuevo_usuario = UsuarioModelo(
            nombre=usuario.nombre,
            email=usuario.email,
            password_hash=usuario.password_hash
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        # Actualizamos el ID del dominio con el generado por la base de datos
        usuario.id = nuevo_usuario.id
        return usuario