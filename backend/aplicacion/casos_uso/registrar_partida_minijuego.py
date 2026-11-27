from datetime import date
from typing import Callable
from dominio.excepciones.errores_dominio import ErrorDominio


class RegistrarPartidaMinijuego:
    def __init__(
        self,
        repo_plantas,
        motor_gamificacion,
        proveedor_fecha: Callable[[], date] = date.today,
    ):
        self.repo_plantas = repo_plantas
        self.motor_gamificacion = motor_gamificacion
        self.proveedor_fecha = proveedor_fecha

    def ejecutar(self, usuario_id: int, planta_id: int, puntaje: int) -> dict:
        if isinstance(puntaje, bool) or not isinstance(puntaje, int) or puntaje < 0:
            raise ErrorDominio("El puntaje debe ser un número entero mayor o igual a 0")

        planta = self.repo_plantas.obtener(planta_id)
        if not planta or not planta.pertenece_a(usuario_id):
            raise ErrorDominio("La planta no existe o no pertenece al usuario")

        hoy = self.proveedor_fecha()
        xp_hoy = planta.xp_minijuego_del_dia(hoy)
        resultado = self.motor_gamificacion.calcular_xp_minijuego(puntaje, xp_hoy)

        if resultado.xp_otorgada > 0:
            planta.registrar_xp_minijuego(resultado.xp_otorgada, hoy)
            self.repo_plantas.actualizar(planta)

        return {
            "xp_ganada": resultado.xp_otorgada,
            "xp_restante_hoy": resultado.xp_restante_hoy,
            "tope_diario_alcanzado": resultado.tope_diario_alcanzado,
            "gamificacion": planta.resumen_gamificacion(),
        }
