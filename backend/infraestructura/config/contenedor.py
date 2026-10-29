import os
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.servicios.generador_recomendaciones import GeneradorRecomendaciones
from aplicacion.casos_uso.registrar_medicion import RegistrarMedicion
from infraestructura.persistencia.sql.repositorio_mediciones_sql import RepositorioMedicionesSQL
from infraestructura.persistencia.sql.tabla_referencia_sql import TablaReferenciaSQL
from infraestructura.persistencia.csv.tabla_referencia_csv import TablaReferenciaCSV

class Contenedor:
    def __init__(self):
        # 1. Instanciar Servicios de Dominio
        estrategia = EstrategiaAgregacionPorConteo()
        generador = GeneradorRecomendaciones()
        self.evaluador = EvaluadorPlanta(estrategia, generador)

        # 2. Configurar Adaptadores de Salida (Infraestructura)
        self.repo_mediciones = RepositorioMedicionesSQL()
        
        # Mocks temporales para lo que aún no hemos programado
        self.repo_plantas = None 
        self.hasher = None
        
        # R4: Intercambiabilidad por configuración (Sin tocar el dominio)
        tipo_persistencia = os.getenv('TIPO_PERSISTENCIA', 'SQL')
        if tipo_persistencia == 'CSV':
            self.tabla_referencia = TablaReferenciaCSV()
        else:
            self.tabla_referencia = TablaReferenciaSQL()

        # 3. Ensamblar los Casos de Uso
        self.registrar_medicion_use_case = RegistrarMedicion(
            repo_plantas=self.repo_plantas,
            hasher_tokens=self.hasher,
            tabla_referencia=self.tabla_referencia,
            evaluador_planta=self.evaluador,
            repo_mediciones=self.repo_mediciones
        )

contenedor_app = Contenedor()
registrar_medicion_use_case = contenedor_app.registrar_medicion_use_case