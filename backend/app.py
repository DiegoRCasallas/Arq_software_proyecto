import os
from flask import Flask, jsonify
from presentacion.controladores.mediciones_controller import dispositivos_bp
from infraestructura.persistencia.sql.modelos import db
from infraestructura.config.contenedor import contenedor_app

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///matera.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Solo crea el esquema si no existe, basándose en los modelos aislados
    with app.app_context():
        db.create_all()

    app.register_blueprint(dispositivos_bp)

    @app.errorhandler(404)
    def no_encontrado(e):
        return jsonify({"error": "RUTA_NO_ENCONTRADA", "mensaje": "El endpoint solicitado no existe"}), 404

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)