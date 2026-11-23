from enum import Enum


class EstadoAnimo(Enum):
    FELIZ = "FELIZ"
    SEDIENTA = "SEDIENTA"        # humedad BAJO
    AHOGADA = "AHOGADA"          # humedad ALTO
    SOFOCADA = "SOFOCADA"        # temperatura ALTO
    CON_FRIO = "CON_FRIO"        # temperatura BAJO
    SIN_LUZ = "SIN_LUZ"          # luz BAJO
    DESLUMBRADA = "DESLUMBRADA"  # luz ALTO
    DORMIDA = "DORMIDA"          # modo nocturno
    EN_RIESGO = "EN_RIESGO"      # fallback genérico
