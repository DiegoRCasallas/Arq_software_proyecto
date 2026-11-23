from datetime import datetime, timedelta
from dominio.entidades.medicion import Medicion
from dominio.servicios.evaluador_fotoperiodo import EvaluadorFotoperiodo
from dominio.valores.estado_parametro import EstadoParametro
from dominio.valores.politica_fotoperiodo import PoliticaFotoperiodo
from dominio.valores.rango_referencia import RangoReferencia


def _rango_luz():
    return RangoReferencia(minimo=300.0, maximo=1500.0)


def _medicion(fecha, luz):
    return Medicion(planta_id=1, fecha=fecha, valores={"luz": luz})


def test_noche_con_poca_luz_y_menos_de_14h_es_reposo_nocturno():
    evaluador = EvaluadorFotoperiodo(PoliticaFotoperiodo(18, 6, 14.0))
    ahora = datetime(2026, 11, 23, 22, 0)  # 10:00 PM
    historial = [_medicion(ahora - timedelta(hours=3), luz=20.0)]

    estado = evaluador.evaluar_luz(
        _medicion(ahora, luz=10.0),
        EstadoParametro.BAJO,
        _rango_luz(),
        historial,
    )
    assert estado == EstadoParametro.REPOSO_NOCTURNO


def test_noche_pero_mas_de_14h_a_oscuras_dispara_alerta_bajo():
    evaluador = EvaluadorFotoperiodo(PoliticaFotoperiodo(18, 6, 14.0))
    ahora = datetime(2026, 11, 23, 22, 0)  # 10:00 PM
    historial = [
        _medicion(ahora - timedelta(hours=5), luz=15.0),
        _medicion(ahora - timedelta(hours=15), luz=10.0),  # 15h continuas sin luz
    ]

    estado = evaluador.evaluar_luz(
        _medicion(ahora, luz=5.0),
        EstadoParametro.BAJO,
        _rango_luz(),
        historial,
    )
    assert estado == EstadoParametro.BAJO


def test_dia_con_poca_luz_siempre_es_bajo():
    evaluador = EvaluadorFotoperiodo(PoliticaFotoperiodo(18, 6, 14.0))
    ahora = datetime(2026, 11, 23, 11, 0)  # 11:00 AM

    estado = evaluador.evaluar_luz(
        _medicion(ahora, luz=50.0),
        EstadoParametro.BAJO,
        _rango_luz(),
        [],
    )
    assert estado == EstadoParametro.BAJO


def test_luz_optima_en_el_historial_reinicia_conteo_de_oscuridad():
    evaluador = EvaluadorFotoperiodo(PoliticaFotoperiodo(18, 6, 14.0))
    ahora = datetime(2026, 11, 23, 23, 0)  # 11:00 PM
    historial = [
        _medicion(ahora - timedelta(hours=4), luz=10.0),   # 7 PM (oscuridad)
        _medicion(ahora - timedelta(hours=8), luz=800.0),  # 3 PM (hubo luz)
        _medicion(ahora - timedelta(hours=20), luz=10.0),  # noche anterior (se ignora)
    ]

    estado = evaluador.evaluar_luz(
        _medicion(ahora, luz=5.0),
        EstadoParametro.BAJO,
        _rango_luz(),
        historial,
    )
    assert estado == EstadoParametro.REPOSO_NOCTURNO
