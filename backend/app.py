import os
from flask import Flask, jsonify
from flask_cors import CORS
from presentacion.controladores.mediciones_controller import dispositivos_bp
from infraestructura.persistencia.sql.modelos import db
from infraestructura.config.contenedor import contenedor_app
from presentacion.controladores.usuarios_controller import usuarios_bp

def crear_app():
    app = Flask(__name__)
    CORS(app)
    
    database_url = os.getenv('DATABASE_URL', 'sqlite:///matera.db')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Solo crea el esquema si no existe, basándose en los modelos aislados
    with app.app_context():
        db.create_all()

    app.register_blueprint(dispositivos_bp)
    app.register_blueprint(usuarios_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/api/v1/seed", methods=["GET", "POST"])
    def seed_db():
        from seed import poblar_datos
        creado = poblar_datos(db)
        if creado:
            return jsonify({"status": "ok", "mensaje": "Base de datos poblada con éxito."}), 200
        return jsonify({"status": "ok", "mensaje": "La base de datos ya contenía los datos iniciales."}), 200

    @app.errorhandler(404)
    def no_encontrado(e):
        return jsonify({"error": "RUTA_NO_ENCONTRADA", "mensaje": "El endpoint solicitado no existe"}), 404

    return app


create_app = crear_app

if __name__ == '__main__':
    app = crear_app()
    app.run(debug=True, host='0.0.0.0', port=5000)