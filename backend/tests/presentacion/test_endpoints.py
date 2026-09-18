import pytest

from app import crear_app


@pytest.fixture
def client():
    app = crear_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"status": "ok"}


def test_listar_especies_devuelve_al_menos_cinco(client):
    respuesta = client.get("/especies")
    assert respuesta.status_code == 200
    especies = respuesta.get_json()
    assert len(especies) >= 5
    assert "especie" in especies[0]
    assert "rangos" in especies[0]


def test_diagnostico_planta_saludable(client):
    payload = {"especie": "albahaca", "humedad": 55, "temperatura": 22, "luz": 12000}
    respuesta = client.post("/diagnostico", json=payload)
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert cuerpo["indice_vitalidad"] == "SALUDABLE"
    assert cuerpo["estados"]["humedad"] == "OPTIMO"
    assert cuerpo["recomendaciones"] == []


def test_diagnostico_planta_en_riesgo(client):
    payload = {"especie": "albahaca", "humedad": 20, "temperatura": 22, "luz": 12000}
    respuesta = client.post("/diagnostico", json=payload)
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert cuerpo["indice_vitalidad"] == "EN_RIESGO"
    assert len(cuerpo["recomendaciones"]) == 1


def test_diagnostico_especie_inexistente_devuelve_404(client):
    payload = {"especie": "dinosaurio", "humedad": 55, "temperatura": 22, "luz": 12000}
    respuesta = client.post("/diagnostico", json=payload)
    assert respuesta.status_code == 404
    cuerpo = respuesta.get_json()
    assert cuerpo["error"] == "ESPECIE_NO_ENCONTRADA"


def test_diagnostico_parametro_ausente_devuelve_400(client):
    payload = {"especie": "albahaca", "humedad": 55, "temperatura": 22}  # falta luz
    respuesta = client.post("/diagnostico", json=payload)
    assert respuesta.status_code == 400
    cuerpo = respuesta.get_json()
    assert cuerpo["error"] == "PARAMETRO_AUSENTE"


def test_diagnostico_valor_no_numerico_devuelve_400(client):
    payload = {"especie": "albahaca", "humedad": "muy húmedo", "temperatura": 22, "luz": 12000}
    respuesta = client.post("/diagnostico", json=payload)
    assert respuesta.status_code == 400
    cuerpo = respuesta.get_json()
    assert cuerpo["error"] == "VALOR_NO_NUMERICO"


def test_diagnostico_valor_fuera_de_rango_fisico_devuelve_400(client):
    payload = {"especie": "albahaca", "humedad": 500, "temperatura": 22, "luz": 12000}
    respuesta = client.post("/diagnostico", json=payload)
    assert respuesta.status_code == 400
    cuerpo = respuesta.get_json()
    assert cuerpo["error"] == "VALOR_FUERA_DE_RANGO_FISICO"


def test_diagnostico_cuerpo_no_json_devuelve_400(client):
    respuesta = client.post("/diagnostico", data="esto no es json", content_type="text/plain")
    assert respuesta.status_code == 400
