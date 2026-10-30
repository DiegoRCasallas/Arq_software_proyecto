from infraestructura.persistencia.sql.modelos import PlantaModelo

class RepositorioPlantasSQL:
    def obtener_por_dispositivo(self, dispositivo_id: str):
        # 1. Buscar en la base de datos
        planta_db = PlantaModelo.query.filter_by(dispositivo_id=dispositivo_id).first()
        
        if not planta_db:
            return None
            
        # 2. Es vital retornar un objeto puro del Dominio, no el modelo de SQLAlchemy
        from dominio.entidades.planta import Planta 
        
        return Planta(
            id=planta_db.id,
            usuario_id=planta_db.usuario_id,
            especie=planta_db.especie,
            apodo=planta_db.apodo,
            dispositivo_id=planta_db.dispositivo_id,
            token_dispositivo_hash=planta_db.token_dispositivo_hash
        )

    def obtener(self, planta_id: int):
        planta_db = PlantaModelo.query.get(planta_id)
        if not planta_db:
            return None
            
        from dominio.entidades.planta import Planta
        return Planta(
            id=planta_db.id,
            usuario_id=planta_db.usuario_id,
            especie=planta_db.especie,
            apodo=planta_db.apodo,
            dispositivo_id=planta_db.dispositivo_id,
            token_dispositivo_hash=planta_db.token_dispositivo_hash
        )