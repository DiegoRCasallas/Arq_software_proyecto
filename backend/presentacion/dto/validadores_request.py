from datetime import datetime
from dominio.entidades.lectura_sensor import Medicion
from dominio.excepciones.errores_dominio import ErrorDominio

def construir_medicion(json_data: dict) -> Medicion:
    valores = json_data.get("valores")
    
    if not valores or not isinstance(valores, dict):
        raise ErrorDominio("El campo 'valores' es obligatorio y debe ser un objeto JSON.")
    
    # Aseguramos que los valores sean numéricos (el sensor envía números)
    try:
        valores_limpios = {k: float(v) for k, v in valores.items()}
    except ValueError:
        raise ErrorDominio("Todos los valores de la medición deben ser numéricos.")

    # Instanciamos la entidad de dominio.
    # El planta_id se inicializa en None porque se asigna después de validar el token en el caso de uso.
    return Medicion(
        planta_id=None,
        fecha=datetime.now(),
        valores=valores_limpios
    )