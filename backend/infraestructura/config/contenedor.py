# Importamos el dominio y casos de uso
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.servicios.generador_recomendaciones import GeneradorRecomendaciones
from aplicacion.casos_uso.registrar_medicion import RegistrarMedicion

# Aquí importaremos los adaptadores (SQL, CSV, JWT) a medida que los construyamos
# Por ahora usaremos "None" o clases falsas rápidas (Mocks) solo para que la app pueda arrancar y no de error de importación.

class Contenedor:
    def __init__(self):
        # 1. Instanciar Servicios de Dominio
        estrategia = EstrategiaAgregacionPorConteo()
        generador = GeneradorRecomendaciones()
        self.evaluador = EvaluadorPlanta(estrategia, generador)

        # 2. Instanciar Adaptadores de Salida (Infraestructura)
        # TODO: Reemplazar estos "None" por las verdaderas clases SQL/CSV cuando las hagamos
        self.repo_plantas = None 
        self.hasher = None
        self.tabla_referencia = None
        self.repo_mediciones = None

        # 3. Ensamblar los Casos de Uso inyectando las dependencias
        self.registrar_medicion_use_case = RegistrarMedicion(
            repo_plantas=self.repo_plantas,
            hasher_tokens=self.hasher,
            tabla_referencia=self.tabla_referencia,
            evaluador_planta=self.evaluador,
            repo_mediciones=self.repo_mediciones
        )

# Creamos una única instancia global del contenedor para que Flask la consuma
contenedor_app = Contenedor()
registrar_medicion_use_case = contenedor_app.registrar_medicion_use_case