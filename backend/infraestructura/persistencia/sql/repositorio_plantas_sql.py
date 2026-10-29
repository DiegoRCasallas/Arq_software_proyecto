from infraestructura.persistencia.sql.modelos import PlantaModelo
# Asumiendo que tienes tu entidad Planta en dominio/entidades/planta.py
# class Planta: id, usuario_id, especie, apodo, dispositivo_id, token_dispositivo_hash

class RepositorioPlantasSQL:
    def obtener_por_dispositivo(self, dispositivo_id: str):
        # 1. Buscar en la base de datos
        planta_db = PlantaModelo.query.filter_by(dispositivo_id=dispositivo_id).first()
        
        if not planta_db:
            return None
            
        # 2. Es vital retornar un objeto puro del Dominio, no el modelo de SQLAlchemy
        # (Dependiendo de cómo esté estructurada tu entidad Planta, instánciala aquí)
        from dominio.entidades.planta import Planta # Asegúrate de que exista
        
        return Planta(
            id=planta_db.id,
            usuario_id=planta_db.usuario_id,
            especie=planta_db.especie,
            apodo=planta_db.apodo,
            dispositivo_id=planta_db.dispositivo_id,
            token_dispositivo_hash=planta_db.token_dispositivo_hash
        )