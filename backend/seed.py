from infraestructura.persistencia.sql.modelos import (
    db, UsuarioModelo, EspecieModelo, PlantaModelo, ParametroModelo, RangoEspecieModelo
)
from werkzeug.security import generate_password_hash

# Rangos de la especie "Cinta": (minimo, optimo_min, optimo_max, maximo)
#   - minimo/maximo: rango FÍSICAMENTE POSIBLE del parámetro. Fuera de él la
#     lectura se rechaza (400) y no se guarda.
#   - optimo_min/optimo_max: rango ideal. Fuera de él la planta está BAJO/ALTO.
_RANGOS_CINTA = {
    "temperatura": (-10.0, 18.0, 24.0, 50.0),
    "humedad": (0.0, 40.0, 60.0, 100.0),
    "luz": (0.0, 500.0, 1000.0, 50000.0),
}


def _sincronizar_rangos(db_instance, especie: str) -> None:
    """
    Alinea los rangos de la especie con _RANGOS_CINTA.

    Permite actualizar una base de datos creada con una versión anterior del
    seed (que usaba límites de tolerancia en lugar de límites físicos) sin
    tener que borrarla: basta volver a ejecutar el seed.
    """
    for parametro, (minimo, optimo_min, optimo_max, maximo) in _RANGOS_CINTA.items():
        fila = db_instance.session.get(RangoEspecieModelo, (especie, parametro))
        if fila is None:
            db_instance.session.add(RangoEspecieModelo(
                especie=especie, parametro=parametro, minimo=minimo,
                optimo_min=optimo_min, optimo_max=optimo_max, maximo=maximo))
        else:
            fila.minimo, fila.optimo_min = minimo, optimo_min
            fila.optimo_max, fila.maximo = optimo_max, maximo
    db_instance.session.commit()


def poblar_datos(db_instance=db):
    """
    Puebla los registros iniciales si no existen. Retorna True si se insertaron datos.
    Si ya existían, solo sincroniza los rangos de la especie y retorna False.
    """
    if EspecieModelo.query.filter_by(nombre="Cinta").first():
        _sincronizar_rangos(db_instance, "Cinta")
        return False

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
    db_instance.session.add_all([
        ParametroModelo(nombre="temperatura", unidad="°C", mensaje_bajo="Frío", mensaje_alto="Calor"),
        ParametroModelo(nombre="humedad", unidad="%", mensaje_bajo="Seco", mensaje_alto="Mucha agua"),
        ParametroModelo(nombre="luz", unidad="lux", mensaje_bajo="Oscuro", mensaje_alto="Mucha luz"),
    ])
    db_instance.session.flush()

    # 5. Crear los Rangos de la especie "Cinta"
    _sincronizar_rangos(db_instance, "Cinta")  # hace el commit
    return True


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
        creado = poblar_datos(db)
        if creado:
            print("✅ Base de datos poblada con éxito. El simulador ya puede enviar datos.")
        else:
            print("ℹ️ La base de datos ya contenía los datos iniciales (rangos sincronizados).")
