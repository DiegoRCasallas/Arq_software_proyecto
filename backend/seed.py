import csv
from pathlib import Path
from infraestructura.persistencia.sql.modelos import (
    db, UsuarioModelo, EspecieModelo, PlantaModelo, ParametroModelo, RangoEspecieModelo
)
from werkzeug.security import generate_password_hash

# Especies de referencia iniciales y sus rangos físicos y óptimos:
#   - minimo/maximo: rango FÍSICAMENTE POSIBLE del parámetro. Fuera de él la
#     lectura se rechaza (400) y no se guarda.
#   - optimo_min/optimo_max: rango ideal. Fuera de él la planta está BAJO/ALTO.
ESPECIES_SEED = {
    "Cinta": {
        "fuente": "Manual Botánico",
        "rangos": {
            "temperatura": (-10.0, 18.0, 24.0, 50.0),
            "humedad": (0.0, 40.0, 60.0, 100.0),
            "luz": (0.0, 500.0, 1000.0, 50000.0),
        },
    },
    "albahaca": {
        "fuente": "UMN Extension - Growing basil in home gardens; Soltech Basil Plant Care",
        "rangos": {
            "temperatura": (-10.0, 18.0, 27.0, 50.0),
            "humedad": (0.0, 40.0, 70.0, 100.0),
            "luz": (0.0, 8000.0, 20000.0, 50000.0),
        },
    },
    "poto": {
        "fuente": "Missouri Botanical Garden - Epipremnum aureum; The Sill - Pothos Care Guide",
        "rangos": {
            "temperatura": (-5.0, 15.0, 29.0, 45.0),
            "humedad": (0.0, 30.0, 60.0, 100.0),
            "luz": (0.0, 1000.0, 10000.0, 30000.0),
        },
    },
    "suculenta": {
        "fuente": "Missouri Botanical Garden - Succulent care guide; The Old Farmer's Almanac - Succulents",
        "rangos": {
            "temperatura": (-5.0, 10.0, 32.0, 50.0),
            "humedad": (0.0, 10.0, 40.0, 100.0),
            "luz": (0.0, 15000.0, 40000.0, 80000.0),
        },
    },
    "helecho": {
        "fuente": "Missouri Botanical Garden - Nephrolepis exaltata; RHS - Growing ferns",
        "rangos": {
            "temperatura": (-5.0, 16.0, 24.0, 40.0),
            "humedad": (0.0, 50.0, 80.0, 100.0),
            "luz": (0.0, 1000.0, 8000.0, 20000.0),
        },
    },
    "orquidea": {
        "fuente": "American Orchid Society - Growing basics; RHS - Orchid care",
        "rangos": {
            "temperatura": (5.0, 18.0, 27.0, 40.0),
            "humedad": (0.0, 35.0, 65.0, 100.0),
            "luz": (0.0, 10000.0, 25000.0, 40000.0),
        },
    },
}

_RANGOS_CINTA = ESPECIES_SEED["Cinta"]["rangos"]


def _obtener_especies_a_sembrar() -> dict:
    """
    Retorna el diccionario de especies a sembrar.
    Comienza con ESPECIES_SEED y, si existe especies.csv, sincroniza cualquier especie adicional.
    """
    datos = dict(ESPECIES_SEED)
    ruta_csv = Path(__file__).resolve().parent / "infraestructura" / "persistencia" / "especies.csv"
    if ruta_csv.is_file():
        try:
            with open(ruta_csv, mode="r", encoding="utf-8-sig", newline="") as f:
                lector = csv.DictReader(f)
                for fila in lector:
                    nombre = fila.get("especie", "").strip()
                    if not nombre:
                        continue
                    fuente = fila.get("fuente", "Referencia botánica")
                    rangos = {}
                    for param in ["temperatura", "humedad", "luz"]:
                        try:
                            rangos[param] = (
                                float(fila[f"{param}_min"]),
                                float(fila[f"{param}_optimo_min"]),
                                float(fila[f"{param}_optimo_max"]),
                                float(fila[f"{param}_max"]),
                            )
                        except (KeyError, ValueError):
                            pass
                    if len(rangos) == 3:
                        datos[nombre] = {"fuente": fuente, "rangos": rangos}
        except Exception:
            pass
    return datos


def _sincronizar_rangos(db_instance, especie: str, rangos: dict = None) -> None:
    """
    Alinea los 3 rangos físicos y óptimos de la especie dada.
    """
    if rangos is None:
        todas = _obtener_especies_a_sembrar()
        rangos = todas.get(especie, {}).get("rangos", _RANGOS_CINTA)

    for parametro, (minimo, optimo_min, optimo_max, maximo) in rangos.items():
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
    Puebla los registros iniciales si no existen y sincroniza todas las especies y rangos.
    Garantiza al menos 5 especies con sus 3 rangos físicos y óptimos cada una.
    Retorna True si se insertó o actualizó algún registro.
    """
    hubo_cambios = False
    especies_a_sembrar = _obtener_especies_a_sembrar()

    # 1. Crear los Parámetros si no existen
    parametros_def = [
        ("temperatura", "°C", "Frío", "Calor"),
        ("humedad", "%", "Seco", "Mucha agua"),
        ("luz", "lux", "Oscuro", "Mucha luz"),
    ]
    for nombre, unidad, mbajo, malto in parametros_def:
        param = db_instance.session.get(ParametroModelo, nombre)
        if param is None:
            db_instance.session.add(ParametroModelo(
                nombre=nombre, unidad=unidad, mensaje_bajo=mbajo, mensaje_alto=malto
            ))
            hubo_cambios = True
    db_instance.session.flush()

    # 2. Crear las Especies y sincronizar sus Rangos (al menos 5 especies)
    for nombre_especie, info in especies_a_sembrar.items():
        esp = db_instance.session.get(EspecieModelo, nombre_especie)
        if esp is None:
            esp = EspecieModelo(nombre=nombre_especie, fuente=info["fuente"])
            db_instance.session.add(esp)
            hubo_cambios = True
        else:
            if esp.fuente != info["fuente"]:
                esp.fuente = info["fuente"]
        db_instance.session.flush()

        # Sincronizar los 3 rangos correspondientes a la especie
        for parametro, (minimo, optimo_min, optimo_max, maximo) in info["rangos"].items():
            fila = db_instance.session.get(RangoEspecieModelo, (nombre_especie, parametro))
            if fila is None:
                db_instance.session.add(RangoEspecieModelo(
                    especie=nombre_especie, parametro=parametro, minimo=minimo,
                    optimo_min=optimo_min, optimo_max=optimo_max, maximo=maximo
                ))
                hubo_cambios = True
            else:
                if (fila.minimo != minimo or fila.optimo_min != optimo_min or
                        fila.optimo_max != optimo_max or fila.maximo != maximo):
                    fila.minimo, fila.optimo_min = minimo, optimo_min
                    fila.optimo_max, fila.maximo = optimo_max, maximo
                    hubo_cambios = True

    # 3. Crear Usuario inicial si no existe
    usuario = UsuarioModelo.query.filter_by(email="prueba@planttech.com").first()
    if usuario is None:
        usuario = UsuarioModelo(
            nombre="Usuario Prueba",
            email="prueba@planttech.com",
            password_hash=generate_password_hash("12345")
        )
        db_instance.session.add(usuario)
        db_instance.session.flush()
        hubo_cambios = True

    # 4. Crear la Planta vinculada al ESP32 del simulador si no existe
    planta = PlantaModelo.query.filter_by(dispositivo_id="ESP32_TEST_001").first()
    if planta is None:
        planta = PlantaModelo(
            usuario_id=usuario.id,
            especie="Cinta",
            apodo="My Lovely Plant",
            dispositivo_id="ESP32_TEST_001",
            token_dispositivo_hash=generate_password_hash("token_secreto_123")
        )
        db_instance.session.add(planta)
        hubo_cambios = True

    db_instance.session.commit()
    return hubo_cambios


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
        creado = poblar_datos(db)
        total_especies = db.session.query(EspecieModelo).count()
        total_rangos = db.session.query(RangoEspecieModelo).count()
        if creado:
            print(f"✅ Base de datos poblada con éxito. Especies: {total_especies}, Rangos: {total_rangos}.")
        else:
            print(f"ℹ️ La base de datos ya contenía los datos sincronizados ({total_especies} especies, {total_rangos} rangos).")
