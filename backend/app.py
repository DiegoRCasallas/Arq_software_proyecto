import os
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import inspect, text
from presentacion.controladores.mediciones_controller import dispositivos_bp
from infraestructura.persistencia.sql.modelos import db
from infraestructura.config.contenedor import contenedor_app
from presentacion.controladores.usuarios_controller import usuarios_bp
from presentacion.controladores.plantas_controller import plantas_bp
from presentacion.controladores.especies_controller import crear_especies_blueprint
from presentacion.ws.mediciones import registrar_websocket

def _asegurar_columnas_plantas(db_instance):
    """Agrega columnas nuevas a 'plantas' si la tabla ya existía sin ellas."""
    inspector = inspect(db_instance.engine)
    if not inspector.has_table("plantas"):
        return

    existentes = {col["name"] for col in inspector.get_columns("plantas")}
    migraciones = {
        "experiencia": "INTEGER NOT NULL DEFAULT 0",
        "nivel": "INTEGER NOT NULL DEFAULT 1",
        "estado_animo": "VARCHAR(30) NOT NULL DEFAULT 'FELIZ'",
        "xp_minijuego_hoy": "INTEGER NOT NULL DEFAULT 0",
        "fecha_ultimo_minijuego": "DATE",
    }
    faltantes = [
        f"ALTER TABLE plantas ADD COLUMN {col} {definicion}"
        for col, definicion in migraciones.items()
        if col not in existentes
    ]
    if not faltantes:
        return

    with db_instance.engine.begin() as conn:
        for sql in faltantes:
            conn.execute(text(sql))


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
        _asegurar_columnas_plantas(db)
        # Asegurar que las especies y rangos de referencia existan al iniciar
        try:
            from seed import poblar_datos
            poblar_datos(db)
        except Exception as e:
            app.logger.warning(f"No se pudo sincronizar seed en inicio: {e}")

    app.register_blueprint(dispositivos_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(plantas_bp)
    app.register_blueprint(
        crear_especies_blueprint(contenedor_app.listar_especies_use_case),
        url_prefix="/api/v1",
    )
    registrar_websocket(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/api/v1/seed", methods=["GET", "POST"])
    def seed_db():
        from seed import poblar_datos
        from infraestructura.persistencia.sql.modelos import EspecieModelo, RangoEspecieModelo
        creado = poblar_datos(db)
        conteo_esp = db.session.query(EspecieModelo).count()
        conteo_rangos = db.session.query(RangoEspecieModelo).count()
        if creado:
            return jsonify({
                "status": "ok",
                "mensaje": f"Base de datos poblada con éxito. Especies: {conteo_esp}, Rangos: {conteo_rangos}."
            }), 200
        return jsonify({
            "status": "ok",
            "mensaje": f"La base de datos ya contenía los datos sincronizados ({conteo_esp} especies, {conteo_rangos} rangos)."
        }), 200

    @app.errorhandler(404)
    def no_encontrado(e):
        return jsonify({"error": "RUTA_NO_ENCONTRADA", "mensaje": "El endpoint solicitado no existe"}), 404

    return app


create_app = crear_app

if __name__ == '__main__':
    app = crear_app()
    app.run(debug=True, host='0.0.0.0', port=5000)