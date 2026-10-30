from dominio.excepciones.errores_dominio import ErrorDominio

class ConsultarHistorial:
    def __init__(self, repo_plantas, repo_mediciones):
        self.repo_plantas = repo_plantas
        self.repo_mediciones = repo_mediciones

    def ejecutar(self, usuario_id: int, planta_id: int, limite: int = 10):
        # 1. Buscar la planta
        planta = self.repo_plantas.obtener(planta_id)
        if not planta:
            raise ErrorDominio("La planta no existe")

        # 2. Regla de negocio: Verificar propiedad
        if not planta.pertenece_a(usuario_id):
            raise ErrorDominio("No tienes permisos para ver el historial de esta planta")

        # 3. Consultar el repositorio de mediciones
        return self.repo_mediciones.historial(planta.id, limite)