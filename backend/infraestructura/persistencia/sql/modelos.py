from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class UsuarioModelo(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    plantas = db.relationship('PlantaModelo', backref='usuario', lazy=True)

class EspecieModelo(db.Model):
    __tablename__ = 'especies'
    nombre = db.Column(db.String, primary_key=True)
    fuente = db.Column(db.String)

    rangos = db.relationship('RangoEspecieModelo', backref='especie_ref', lazy=True)

class ParametroModelo(db.Model):
    __tablename__ = 'parametros'
    nombre = db.Column(db.String, primary_key=True)
    unidad = db.Column(db.String)
    mensaje_bajo = db.Column(db.String)
    mensaje_alto = db.Column(db.String)

class RangoEspecieModelo(db.Model):
    __tablename__ = 'rangos_especie'
    especie = db.Column(db.String, db.ForeignKey('especies.nombre'), primary_key=True)
    parametro = db.Column(db.String, db.ForeignKey('parametros.nombre'), primary_key=True)
    minimo = db.Column(db.Float)
    optimo_min = db.Column(db.Float)
    optimo_max = db.Column(db.Float)
    maximo = db.Column(db.Float)

class PlantaModelo(db.Model):
    __tablename__ = 'plantas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    especie = db.Column(db.String, db.ForeignKey('especies.nombre'), nullable=False)
    apodo = db.Column(db.String)
    dispositivo_id = db.Column(db.String, unique=True)
    token_dispositivo_hash = db.Column(db.String)

    mediciones = db.relationship('MedicionModelo', backref='planta', lazy=True)

class MedicionModelo(db.Model):
    __tablename__ = 'mediciones'
    id = db.Column(db.Integer, primary_key=True)
    planta_id = db.Column(db.Integer, db.ForeignKey('plantas.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    valores = db.relationship('ValorMedicionModelo', backref='medicion', lazy=True)

class ValorMedicionModelo(db.Model):
    __tablename__ = 'valores_medicion'
    medicion_id = db.Column(db.Integer, db.ForeignKey('mediciones.id'), primary_key=True)
    parametro = db.Column(db.String, db.ForeignKey('parametros.nombre'), primary_key=True)
    valor = db.Column(db.Float, nullable=False)