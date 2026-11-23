from typing import Optional
from datetime import date
from typing import Optional
from dominio.valores.estado_animo import EstadoAnimo
from dominio.valores.estado_animo import EstadoAnimo

class Planta:
    def __init__(
        self,
        id: Optional[int],
        usuario_id: int,
        especie: str,
        apodo: Optional[str] = None,
        dispositivo_id: Optional[str] = None,
        token_dispositivo_hash: Optional[str] = None,
        experiencia: int = 0, 
        nivel: int = 1, 
        estado_animo: EstadoAnimo = EstadoAnimo.FELIZ
        xp_minijuego_hoy: int = 0, 
        fecha_ultimo_minijuego: Optional[date] = None
    ):
        self.id = id
        self.usuario_id = usuario_id
        self.especie = especie
        self.apodo = apodo
        self.dispositivo_id = dispositivo_id
        self.token_dispositivo_hash = token_dispositivo_hash

    def pertenece_a(self, usuario_id: int) -> bool:
        """Regla de negocio: Verifica si la planta pertenece a un usuario específico"""
        return self.usuario_id == usuario_id
        
    def aplicar_experiencia(self, delta: int) -> None:
        """Suma o resta XP sin permitir puntajes negativos y recalcula el nivel."""
        self.experiencia = max(0, self.experiencia + delta)
        self.nivel = 1 + (self.experiencia // 100)  # Sube de nivel cada 100 XP

    def actualizar_animo(self, nuevo_animo: EstadoAnimo) -> None:
        self.estado_animo = nuevo_animo

    def xp_minijuego_del_dia(self, hoy: date) -> int:
        if self.fecha_ultimo_minijuego != hoy:
            return 0
        return self.xp_minijuego_hoy

    def registrar_xp_minijuego(self, xp: int, hoy: date) -> None:
        if self.fecha_ultimo_minijuego != hoy:
            self.xp_minijuego_hoy = 0
            self.fecha_ultimo_minijuego = hoy
        self.xp_minijuego_hoy += xp
        self.aplicar_experiencia(xp)

    def resumen_gamificacion(self) -> dict:
        xp_en_nivel = self.experiencia % 100
        return {
            "experiencia": self.experiencia,
            "nivel": self.nivel,
            "xp_nivel_actual": xp_en_nivel,
            "xp_siguiente_nivel": 100,
            "porcentaje_nivel": xp_en_nivel,
            "estado_animo": self.estado_animo.value,
        }
