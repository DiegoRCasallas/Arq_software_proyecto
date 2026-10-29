from flask_sqlalchemy import SQLAlchemy
from dominio.entidades.lectura_sensor import Medicion

# Instancia global de SQLAlchemy que luego conectaremos en app.py
db = SQLAlchemy()

# 1. El Modelo de Base de Datos (Tablas reales en SQL)
class MedicionModelo(db.Model):
    __tablename__ = 'mediciones'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    planta_id = db.Column(db.String(50), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False)
    # Guardamos los valores dinámicos como JSON para no limitar los parámetros (humedad, luz, etc.)
    valores = db.Column(db.JSON, nullable=False) 

# 2. El Adaptador que cumple el contrato del Puerto
class RepositorioMedicionesSQL:
    """
    Este es el Adaptador de Salida. El dominio llama a 'guardar', 
    y esta clase se encarga de traducirlo a comandos SQL de SQLAlchemy.
    """
    def guardar(self, medicion: Medicion):
        nueva_medicion = MedicionModelo(
            planta_id=medicion.planta_id,
            fecha=medicion.fecha,
            valores=medicion.valores
        )
        db.session.add(nueva_medicion)
        db.session.commit()

    def historial(self, planta_id: str, limite: int = 50):
        # Consulta SQL para traer el historial ordenado por fecha
        registros = MedicionModelo.query.filter_by(planta_id=planta_id).order_by(MedicionModelo.fecha.desc()).limit(limite).all()
        
        # Transformamos los registros SQL de vuelta a objetos puros del dominio
        return [Medicion(planta_id=r.planta_id, fecha=r.fecha, valores=r.valores) for r in registros]