from dominio.excepciones.errores_dominio import ErrorDominio # Asumiendo que crearás excepciones específicas
from dominio.servicios.evaluador_planta import EvaluadorPlanta

class RegistrarMedicion:
    def __init__(self, 
                 repo_plantas, 
                 hasher_tokens, 
                 tabla_referencia, 
                 evaluador_planta: EvaluadorPlanta, 
                 repo_mediciones):
        # Inyección de dependencias (Puertos)
        self.repo_plantas = repo_plantas
        self.hasher_tokens = hasher_tokens
        self.tabla_referencia = tabla_referencia
        self.evaluador_planta = evaluador_planta
        self.repo_mediciones = repo_mediciones

    def ejecutar(self, dispositivo_id: str, token_plano: str, medicion):
        # 1. Obtener la planta asociada al ESP32
        planta = self.repo_plantas.obtener_por_dispositivo(dispositivo_id)
        if not planta:
            raise ErrorDominio(f"No existe una planta vinculada al dispositivo {dispositivo_id}")

        # 2. Verificar que el token enviado por el ESP32 coincida con el hash guardado (Seguridad JWT/Dispositivo)
        if not self.hasher_tokens.verificar(token_plano, planta.token_dispositivo_hash):
            raise ErrorDominio("Token de dispositivo inválido o no autorizado")

        # 3. Traer los rangos ideales (CSV o BD) sin saber qué tecnología hay detrás
        perfil_especie = self.tabla_referencia.obtener_perfil(planta.especie)
        if not perfil_especie:
            raise ErrorDominio(f"No hay perfil de referencia para la especie {planta.especie}")

        # 4. Asignar el ID de la planta a la medición y evaluar el estado
        medicion.planta_id = planta.id
        diagnostico = self.evaluador_planta.evaluar(medicion, perfil_especie)

        # 5. Guardar la medición en el historial
        self.repo_mediciones.guardar(medicion)

        # 6. Retornar el diagnóstico para que el controlador lo envíe de vuelta (o al frontend)
        return diagnostico