"""
RegistrarMedicion: caso de uso que recibe una medición de un dispositivo.

Orden deliberado de los pasos:
  1. Autenticar el dispositivo (barato de rechazar y no filtra información).
  2. Obtener el perfil de la especie.
  3. Validar la medición contra el perfil (parámetros, completitud, rango físico).
  4. Evaluar y guardar.

Nada se guarda si alguna validación falla.
"""
from dominio.entidades.medicion import Medicion
from dominio.entidades.diagnostico_planta import DiagnosticoPlanta
from dominio.excepciones.errores_dominio import DispositivoNoAutorizado
from dominio.puertos.hasher_contrasenas import HasherContrasenas
from dominio.puertos.repositorio_mediciones import RepositorioMediciones
from dominio.puertos.repositorio_plantas import RepositorioPlantas
from dominio.puertos.tabla_referencia import TablaReferencia
from dominio.servicios.evaluador_planta import EvaluadorPlanta


class RegistrarMedicion:
    def __init__(self,
                 repo_plantas: RepositorioPlantas,
                 hasher_tokens: HasherContrasenas,
                 tabla_referencia: TablaReferencia,
                 evaluador_planta: EvaluadorPlanta,
                 repo_mediciones: RepositorioMediciones):
        # Inyección de dependencias (Puertos)
        self.repo_plantas = repo_plantas
        self.hasher_tokens = hasher_tokens
        self.tabla_referencia = tabla_referencia
        self.evaluador_planta = evaluador_planta
        self.repo_mediciones = repo_mediciones

    def ejecutar(self, dispositivo_id: str, token_plano: str, medicion: Medicion) -> DiagnosticoPlanta:
        # 1. Autenticar al dispositivo. "No existe" y "token incorrecto" son
        #    indistinguibles para quien llama (ver DispositivoNoAutorizado).
        planta = self.repo_plantas.obtener_por_dispositivo(dispositivo_id)
        if planta is None or not self.hasher_tokens.verificar(token_plano, planta.token_dispositivo_hash):
            raise DispositivoNoAutorizado()

        # 2. Rangos de la especie, sin saber si vienen de CSV o de BD.
        #    El puerto lanza EspecieNoEncontrada si no existe.
        perfil_especie = self.tabla_referencia.obtener_perfil(planta.especie)

        # 3. Rechazar lo que no se debe aceptar ni guardar.
        perfil_especie.validar_medicion(medicion)

        # 4. Evaluar y guardar en el historial.
        medicion.planta_id = planta.id
        diagnostico = self.evaluador_planta.evaluar(medicion, perfil_especie)
        self.repo_mediciones.guardar(medicion)

        return diagnostico
