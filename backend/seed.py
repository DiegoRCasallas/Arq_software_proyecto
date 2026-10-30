from infraestructura.persistencia.sql.modelos import (
    db, UsuarioModelo, EspecieModelo, PlantaModelo, ParametroModelo, RangoEspecieModelo
)
from werkzeug.security import generate_password_hash

def poblar_datos(db_instance=db):
    """
    Puebla los registros iniciales si no existen. Retorna True si se insertaron datos.
    """
    if not EspecieModelo.query.filter_by(nombre="Cinta").first():
        # 1. Crear un Usuario
        usuario = UsuarioModelo(
            nombre="Usuario Prueba",
            email="prueba@planttech.com",
            password_hash=generate_password_hash("12345")
        )
        db_instance.session.add(usuario)
        db_instance.session.flush()

        # 2. Crear la Especie
        especie = EspecieModelo(nombre="Cinta", fuente="Manual Botánico")
        db_instance.session.add(especie)
        db_instance.session.flush()

        # 3. Crear la Planta vinculada al ESP32 del simulador
        planta = PlantaModelo(
            usuario_id=usuario.id,
            especie=especie.nombre,
            apodo="My Lovely Plant",
            dispositivo_id="ESP32_TEST_001",
            token_dispositivo_hash=generate_password_hash("token_secreto_123")
        )
        db_instance.session.add(planta)

        # 4. Crear los Parámetros
        p_temp = ParametroModelo(nombre="temperatura", unidad="°C", mensaje_bajo="Frío", mensaje_alto="Calor")
        p_hum = ParametroModelo(nombre="humedad", unidad="%", mensaje_bajo="Seco", mensaje_alto="Mucha agua")
        p_luz = ParametroModelo(nombre="luz", unidad="lux", mensaje_bajo="Oscuro", mensaje_alto="Mucha luz")
        db_instance.session.add_all([p_temp, p_hum, p_luz])
        db_instance.session.flush()

        # 5. Crear los Rangos Ideales de la Especie "Cinta"
        r_temp = RangoEspecieModelo(especie="Cinta", parametro="temperatura", minimo=10.0, optimo_min=18.0, optimo_max=24.0, maximo=35.0)
        r_hum = RangoEspecieModelo(especie="Cinta", parametro="humedad", minimo=20.0, optimo_min=40.0, optimo_max=60.0, maximo=80.0)
        r_luz = RangoEspecieModelo(especie="Cinta", parametro="luz", minimo=200.0, optimo_min=500.0, optimo_max=1000.0, maximo=2000.0)
        db_instance.session.add_all([r_temp, r_hum, r_luz])

        db_instance.session.commit()
        return True
    return False

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
        creado = poblar_datos(db)
        if creado:
            print("✅ Base de datos poblada con éxito. El simulador ya puede enviar datos.")
        else:
            print("ℹ️ La base de datos ya contenía los datos iniciales.")