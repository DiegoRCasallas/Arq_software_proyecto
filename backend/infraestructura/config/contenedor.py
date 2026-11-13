import os
from dominio.servicios.evaluador_planta import EvaluadorPlanta
from dominio.servicios.estrategia_agregacion_por_conteo import EstrategiaAgregacionPorConteo
from dominio.servicios.generador_recomendaciones import GeneradorRecomendaciones
from aplicacion.casos_uso.registrar_medicion import RegistrarMedicion
from infraestructura.persistencia.sql.repositorio_mediciones_sql import RepositorioMedicionesSQL
from infraestructura.persistencia.sql.tabla_referencia_sql import TablaReferenciaSQL
from infraestructura.persistencia.csv.tabla_referencia_csv import TablaReferenciaCSV
from infraestructura.persistencia.sql.repositorio_plantas_sql import RepositorioPlantasSQL
from infraestructura.seguridad.hasher_werkzeug import HasherWerkzeug
from aplicacion.casos_uso.consultar_historial import ConsultarHistorial
from aplicacion.casos_uso.listar_especies import ListarEspeciesUseCase

class Contenedor:
    def __init__(self):
        # 1. Instanciar Servicios de Dominio
        estrategia = EstrategiaAgregacionPorConteo()
        generador = GeneradorRecomendaciones()
        self.evaluador = EvaluadorPlanta(estrategia, generador)

        # 2. Configurar Adaptadores de Salida (Infraestructura)
        self.repo_mediciones = RepositorioMedicionesSQL()
        self.repo_plantas = RepositorioPlantasSQL()
        self.hasher = HasherWerkzeug()
        
        # Intercambiabilidad R4
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

        # 4. Configurar Adaptadores de Seguridad y Usuarios
        from infraestructura.persistencia.sql.repositorio_usuarios_sql import RepositorioUsuariosSQL
        from infraestructura.seguridad.tokens_jwt import TokensJWT
        from aplicacion.casos_uso.registrar_usuario import RegistrarUsuario
        from aplicacion.casos_uso.iniciar_sesion import IniciarSesion

        self.repo_usuarios = RepositorioUsuariosSQL()
        self.servicio_tokens = TokensJWT()

        self.registrar_usuario_use_case = RegistrarUsuario(
            repo_usuarios=self.repo_usuarios,
            hasher_contrasenas=self.hasher
        )

        self.iniciar_sesion_use_case = IniciarSesion(
            repo_usuarios=self.repo_usuarios,
            hasher_contrasenas=self.hasher,
            servicio_tokens=self.servicio_tokens
        )

        self.consultar_historial_use_case = ConsultarHistorial(
            repo_plantas=self.repo_plantas,
            repo_mediciones=self.repo_mediciones,
            tabla_referencia=self.tabla_referencia,
            evaluador=self.evaluador
        )

        self.listar_especies_use_case = ListarEspeciesUseCase(
            tabla_referencia=self.tabla_referencia
        )

        # 5. Casos de uso de vinculación de dispositivos (QR)
        from aplicacion.casos_uso.vincular_dispositivo import VincularDispositivo
        from aplicacion.casos_uso.desvincular_dispositivo import DesvincularDispositivo

        self.vincular_dispositivo_use_case = VincularDispositivo(
            repo_plantas=self.repo_plantas,
            hasher=self.hasher,
        )
        self.desvincular_dispositivo_use_case = DesvincularDispositivo(
            repo_plantas=self.repo_plantas,
        )

contenedor_app = Contenedor()
registrar_medicion_use_case = contenedor_app.registrar_medicion_use_case