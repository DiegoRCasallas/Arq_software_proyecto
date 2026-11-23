import pytest
from datetime import date
from dominio.entidades.diagnostico_planta import DiagnosticoPlanta
from dominio.entidades.planta import Planta
from dominio.servicios.motor_gamificacion import MotorGamificacion
from dominio.valores.estado_animo import EstadoAnimo
from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.estado_planta import EstadoPlanta


def _diagnostico(estado_planta, **estados):
    return DiagnosticoPlanta(
        estado_planta=estado_planta,
        estados=estados,
        recomendaciones=[],
    )


def test_medicion_optima_suma_10_xp_y_animo_feliz():
    motor = MotorGamificacion()
    diag = _diagnostico(
        EstadoPlanta.SALUDABLE,
        temperatura=EstadoParametro.OPTIMO,
        humedad=EstadoParametro.OPTIMO,
        luz=EstadoParametro.OPTIMO,
    )

    res = motor.calcular(diag)
    assert res.delta_xp == 10
    assert res.estado_animo == EstadoAnimo.FELIZ


def test_riego_exitoso_suma_50_xp():
    motor = MotorGamificacion()
    anterior = _diagnostico(EstadoPlanta.EN_RIESGO, humedad=EstadoParametro.BAJO)
    actual = _diagnostico(EstadoPlanta.SALUDABLE, humedad=EstadoParametro.OPTIMO)

    res = motor.calcular(actual, anterior)
    assert res.delta_xp == 50
    assert res.estado_animo == EstadoAnimo.FELIZ


@pytest.mark.parametrize(
    "estados,animo_esperado",
    [
        ({"humedad": EstadoParametro.BAJO}, EstadoAnimo.SEDIENTA),
        ({"humedad": EstadoParametro.ALTO}, EstadoAnimo.AHOGADA),
        ({"temperatura": EstadoParametro.ALTO}, EstadoAnimo.SOFOCADA),
        ({"temperatura": EstadoParametro.BAJO}, EstadoAnimo.CON_FRIO),
        ({"luz": EstadoParametro.BAJO}, EstadoAnimo.SIN_LUZ),
        ({"luz": EstadoParametro.ALTO}, EstadoAnimo.DESLUMBRADA),
    ],
)
def test_cada_parametro_asigna_su_contraparte_de_animo(estados, animo_esperado):
    motor = MotorGamificacion()
    diag = _diagnostico(EstadoPlanta.EN_RIESGO, **estados)

    res = motor.calcular(diag)
    assert res.delta_xp == -10
    assert res.estado_animo == animo_esperado


def test_experiencia_no_baja_de_cero_y_sube_de_nivel():
    planta = Planta(id=1, usuario_id=1, especie="Cinta", apodo="Lola")

    planta.aplicar_experiencia(-50)
    assert planta.experiencia == 0
    assert planta.nivel == 1

    planta.aplicar_experiencia(120)
    assert planta.experiencia == 120
    assert planta.nivel == 2
    assert planta.resumen_gamificacion()["xp_nivel_actual"] == 20


def test_minijuego_respeta_tope_por_partida_y_tope_diario():
    motor = MotorGamificacion()

    # Puntaje altísimo no supera el tope por partida (30 XP)
    r1 = motor.calcular_xp_minijuego(puntaje=999, xp_ganada_hoy=0)
    assert r1.xp_otorgada == 30
    assert r1.xp_restante_hoy == 30
    assert not r1.tope_diario_alcanzado

    # Cuando solo quedan 10 XP disponibles hoy, recorta la recompensa
    r2 = motor.calcular_xp_minijuego(puntaje=150, xp_ganada_hoy=50)
    assert r2.xp_otorgada == 10
    assert r2.xp_restante_hoy == 0
    assert r2.tope_diario_alcanzado

    # Si ya llegó al tope diario, otorga 0
    r3 = motor.calcular_xp_minijuego(puntaje=100, xp_ganada_hoy=60)
    assert r3.xp_otorgada == 0
    assert r3.tope_diario_alcanzado


def test_planta_reinicia_contador_minijuego_al_cambiar_de_dia():
    planta = Planta(id=1, usuario_id=1, especie="Cinta", apodo="Lola")
    dia_1 = date(2026, 11, 23)
    dia_2 = date(2026, 11, 24)

    planta.registrar_xp_minijuego(30, dia_1)
    assert planta.xp_minijuego_del_dia(dia_1) == 30
    assert planta.xp_minijuego_del_dia(dia_2) == 0
