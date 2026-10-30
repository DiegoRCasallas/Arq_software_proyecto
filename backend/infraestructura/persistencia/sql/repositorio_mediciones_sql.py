from dominio.entidades.medicion import Medicion
from infraestructura.persistencia.sql.modelos import db, MedicionModelo, ValorMedicionModelo

class RepositorioMedicionesSQL:
    """
    Adaptador de salida para persistir mediciones en PostgreSQL/SQLite.
    Implementa la interfaz (puerto) RepositorioMediciones del dominio.
    """
    
    def guardar(self, medicion: Medicion) -> None:
        # 1. Crear el registro principal de la medición
        nueva_medicion = MedicionModelo(
            planta_id=medicion.planta_id,
            fecha=medicion.fecha
        )
        db.session.add(nueva_medicion)
        db.session.flush()  # Empuja a la BD para obtener nueva_medicion.id sin cerrar la transacción
        
        # 2. Guardar cada valor dinámico como una fila independiente en VALORES_MEDICION
        for parametro, valor in medicion.valores.items():
            nuevo_valor = ValorMedicionModelo(
                medicion_id=nueva_medicion.id,
                parametro=parametro,
                valor=valor
            )
            db.session.add(nuevo_valor)
            
        db.session.commit()

    def historial(self, planta_id: int, limite: int = 50) -> list[Medicion]:
        # 1. Traer las mediciones base ordenadas por fecha descendente
        registros = MedicionModelo.query.filter_by(planta_id=planta_id)\
                                        .order_by(MedicionModelo.fecha.desc())\
                                        .limit(limite).all()
        
        resultado = []
        for reg in registros:
            # 2. Reconstruir el diccionario de valores leyendo la relación uno a muchos
            valores_dict = {v.parametro: v.valor for v in reg.valores}
            
            # 3. Mapear de vuelta al objeto puro del dominio
            medicion_obj = Medicion(
                planta_id=reg.planta_id,
                fecha=reg.fecha,
                valores=valores_dict
            )
            resultado.append(medicion_obj)
            
        return resultado