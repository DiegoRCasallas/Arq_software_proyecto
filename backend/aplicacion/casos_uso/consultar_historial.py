from dominio.excepciones.errores_dominio import ErrorDominio

class ConsultarHistorial:
    def __init__(self, repo_plantas, repo_mediciones, tabla_referencia, evaluador):
        self.repo_plantas = repo_plantas
        self.repo_mediciones = repo_mediciones
        self.tabla_referencia = tabla_referencia
        self.evaluador = evaluador

    def ejecutar(self, usuario_id: int, planta_id: int, limite: int = 10):
        # 1. Buscar la planta y verificar propiedad
        planta = self.repo_plantas.obtener(planta_id)
        if not planta:
            raise ErrorDominio("La planta no existe")
        if not planta.pertenece_a(usuario_id):
            raise ErrorDominio("No tienes permisos para ver el historial de esta planta")

        # 2. Obtener el perfil con los rangos ideales de su especie
        perfil_especie = self.tabla_referencia.obtener_perfil(planta.especie)
        if not perfil_especie:
            raise ErrorDominio("No hay datos de referencia para esta especie")

        # 3. Obtener mediciones crudas
        mediciones_crudas = self.repo_mediciones.historial(planta.id, limite)

        # 4. Evaluar cada medición usando el servicio del Dominio
        historial_evaluado = []
        for medicion in mediciones_crudas:
            diagnostico = self.evaluador.evaluar(medicion, perfil_especie)
            historial_evaluado.append({
                "medicion": medicion,
                "diagnostico": diagnostico
            })

        return historial_evaluado