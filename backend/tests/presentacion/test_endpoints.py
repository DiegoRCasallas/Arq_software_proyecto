import pytest

from infraestructura.persistencia.sql.modelos import MedicionModelo

URL = "/api/v1/dispositivos/ESP32_TEST_001/mediciones"
HEADERS = {"X-Device-Token": "token_secreto_123"}
NORMAL = {"temperatura": 22, "humedad": 50, "luz": 800}


def enviar(client, valores, headers=HEADERS, url=URL):
    return client.post(url, json={"valores": valores}, headers=headers)


def contar_mediciones(app):
    with app.app_context():
        return MedicionModelo.query.count()


# --------------------------------------------------------------------------- #
# Endpoints generales
# --------------------------------------------------------------------------- #
def test_health(client):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"status": "ok"}


def test_listar_especies(client):
    respuesta = client.get("/api/v1/especies")

    assert respuesta.status_code == 200
    especies = respuesta.get_json()
    assert [e["especie"] for e in especies] == ["Cinta"]
    assert set(especies[0]["rangos"]) == {"temperatura", "humedad", "luz"}
    assert set(especies[0]["rangos"]["luz"]) == {"minimo", "optimo_min", "optimo_max", "maximo"}


def test_ruta_inexistente_devuelve_json_404(client):
    assert client.post("/diagnostico", json={}).status_code == 404  # endpoint de la Fase 1, eliminado


# --------------------------------------------------------------------------- #
# Mediciones aceptadas
# --------------------------------------------------------------------------- #
def test_medicion_normal_es_saludable_y_se_guarda(app, client):
    respuesta = enviar(client, NORMAL)

    assert respuesta.status_code == 201
    cuerpo = respuesta.get_json()
    assert cuerpo["estado_general"] == "SALUDABLE"
    assert cuerpo["detalle_parametros"] == {"temperatura": "OPTIMO", "humedad": "OPTIMO", "luz": "OPTIMO"}
    assert cuerpo["recomendaciones"] == []
    assert contar_mediciones(app) == 1


def test_medicion_anomala_pero_posible_es_critica_y_se_guarda(app, client):
    respuesta = enviar(client, {"temperatura": 40, "humedad": 10, "luz": 9000})

    assert respuesta.status_code == 201
    cuerpo = respuesta.get_json()
    assert cuerpo["estado_general"] == "CRITICO"
    assert len(cuerpo["recomendaciones"]) == 3
    assert contar_mediciones(app) == 1


@pytest.mark.parametrize("valores", [
    {"temperatura": -10, "humedad": 0, "luz": 0},          # límites físicos inferiores exactos
    {"temperatura": 50, "humedad": 100, "luz": 50000},     # límites físicos superiores exactos
    {"temperatura": "22.5", "humedad": "50", "luz": "800"},  # números como texto
])
def test_valores_validos_en_los_bordes_son_aceptados(client, valores):
    assert enviar(client, valores).status_code == 201


# --------------------------------------------------------------------------- #
# Mediciones rechazadas: 400, código de error claro y NADA se guarda
# --------------------------------------------------------------------------- #
CASOS_RECHAZADOS = [
    # (id, valores, codigo_de_error)
    ("null (sensor desconectado)", {"temperatura": None, "humedad": 50, "luz": 800}, "VALOR_NO_NUMERICO"),
    ("solo null", {"temperatura": None}, "VALOR_NO_NUMERICO"),
    ("texto", {"temperatura": "texto_roto", "humedad": 50, "luz": 800}, "VALOR_NO_NUMERICO"),
    ("'nan' como texto", {"temperatura": "nan", "humedad": 50, "luz": 800}, "VALOR_NO_NUMERICO"),
    ("'inf' como texto", {"temperatura": "inf", "humedad": 50, "luz": 800}, "VALOR_NO_NUMERICO"),
    ("booleano", {"temperatura": True, "humedad": 50, "luz": 800}, "VALOR_NO_NUMERICO"),
    ("lista", {"temperatura": [22], "humedad": 50, "luz": 800}, "VALOR_NO_NUMERICO"),
    ("objeto", {"temperatura": {"v": 22}, "humedad": 50, "luz": 800}, "VALOR_NO_NUMERICO"),
    ("parametro desconocido", {**NORMAL, "ph": 7.0}, "PARAMETRO_DESCONOCIDO"),
    ("solo parametros desconocidos", {"ph": 7.0}, "PARAMETRO_DESCONOCIDO"),
    ("parametro ausente", {"temperatura": 22}, "PARAMETRO_AUSENTE"),
    ("valores vacio", {}, "PARAMETRO_AUSENTE"),
    ("temperatura imposible", {**NORMAL, "temperatura": 9999}, "VALOR_FUERA_DE_RANGO_FISICO"),
    ("humedad negativa", {**NORMAL, "humedad": -5}, "VALOR_FUERA_DE_RANGO_FISICO"),
    ("humedad > 100%", {**NORMAL, "humedad": 100.5}, "VALOR_FUERA_DE_RANGO_FISICO"),
]


@pytest.mark.parametrize("valores,codigo", [(v, c) for _, v, c in CASOS_RECHAZADOS],
                         ids=[i for i, _, _ in CASOS_RECHAZADOS])
def test_medicion_invalida_devuelve_400_y_no_se_guarda(app, client, valores, codigo):
    respuesta = enviar(client, valores)

    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"] == codigo
    assert contar_mediciones(app) == 0


def test_nan_numerico_en_el_json_devuelve_400_y_no_500(app, client):
    # Un firmware que serializa NaN produce este JSON (no estándar, pero Python lo acepta).
    cuerpo = '{"valores": {"temperatura": NaN, "humedad": 50, "luz": 800}}'
    respuesta = client.post(URL, data=cuerpo, headers={**HEADERS, "Content-Type": "application/json"})

    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"] == "VALOR_NO_NUMERICO"
    assert contar_mediciones(app) == 0


@pytest.mark.parametrize("cuerpo,content_type", [
    ("esto no es json", "text/plain"),
    ("5", "application/json"),
    ("[1, 2, 3]", "application/json"),
    ('{"temperatura": 22}', "application/json"),                 # sin la clave "valores"
    ('{"valores": [22, 50, 800]}', "application/json"),          # "valores" no es un objeto
    ("", "application/json"),
])
def test_cuerpo_con_forma_invalida_devuelve_400_json_y_no_500(app, client, cuerpo, content_type):
    respuesta = client.post(URL, data=cuerpo, headers={**HEADERS, "Content-Type": content_type})

    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"] == "PARAMETRO_AUSENTE"
    assert contar_mediciones(app) == 0


# --------------------------------------------------------------------------- #
# Autenticación del dispositivo
# --------------------------------------------------------------------------- #
def test_sin_token_devuelve_401(app, client):
    respuesta = client.post(URL, json={"valores": NORMAL})

    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"] == "AUTORIZACION_DENEGADA"
    assert contar_mediciones(app) == 0


def test_token_incorrecto_devuelve_401(app, client):
    respuesta = enviar(client, NORMAL, headers={"X-Device-Token": "incorrecto"})

    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"] == "DISPOSITIVO_NO_AUTORIZADO"
    assert contar_mediciones(app) == 0


def test_dispositivo_inexistente_responde_igual_que_token_incorrecto(client):
    """Mismo código y mismo cuerpo: no se puede averiguar qué dispositivos existen."""
    por_token = enviar(client, NORMAL, headers={"X-Device-Token": "incorrecto"})
    por_dispositivo = enviar(client, NORMAL, url="/api/v1/dispositivos/NO_EXISTE/mediciones")

    assert por_dispositivo.status_code == por_token.status_code == 401
    assert por_dispositivo.get_json() == por_token.get_json()


# --------------------------------------------------------------------------- #
# Flujo completo: lo que envía el sensor es lo que ve el frontend
# --------------------------------------------------------------------------- #
def test_las_mediciones_aceptadas_aparecen_en_el_historial_y_las_rechazadas_no(client):
    enviar(client, NORMAL)                                          # aceptada
    enviar(client, {"temperatura": None, "humedad": 50, "luz": 800})   # rechazada
    enviar(client, {**NORMAL, "temperatura": 9999})                 # rechazada
    enviar(client, {"temperatura": 40, "humedad": 10, "luz": 9000})    # aceptada

    login = client.post("/api/v1/usuarios/login",
                        json={"email": "prueba@planttech.com", "contrasena": "12345"})
    assert login.status_code == 200
    token = login.get_json()["token"]

    historial = client.get("/api/v1/plantas/1/historial", headers={"Authorization": f"Bearer {token}"})

    assert historial.status_code == 200
    registros = historial.get_json()
    assert len(registros) == 2
    assert {r["estado_general"] for r in registros} == {"SALUDABLE", "CRITICO"}


def autenticar(client, email="prueba@planttech.com", contrasena="12345"):
    respuesta = client.post(
        "/api/v1/usuarios/login",
        json={"email": email, "contrasena": contrasena},
    )
    assert respuesta.status_code == 200
    return {"Authorization": f"Bearer {respuesta.get_json()['token']}"}


def test_endpoints_de_plantas_requieren_jwt(client):
    assert client.get("/api/v1/plantas").status_code == 401
    assert client.post("/api/v1/plantas", json={"especie": "Cinta"}).status_code == 401


def test_listado_de_plantas_incluye_la_ultima_medicion_y_su_diagnostico(client):
    enviar(client, NORMAL)
    headers = autenticar(client)

    respuesta = client.get("/api/v1/plantas", headers=headers)

    assert respuesta.status_code == 200
    planta = respuesta.get_json()[0]
    assert planta["ultima_medicion"]["valores"] == NORMAL
    assert planta["ultima_medicion"]["estado_general"] == "SALUDABLE"


def test_usuario_puede_crear_listar_ver_y_borrar_una_planta(client):
    headers = autenticar(client)

    creada = client.post(
        "/api/v1/plantas",
        json={"especie": "Cinta", "apodo": "Cinta del balcón"},
        headers=headers,
    )
    assert creada.status_code == 201
    planta = creada.get_json()
    assert planta["especie"] == "Cinta"
    assert planta["apodo"] == "Cinta del balcón"
    assert planta["dispositivo_conectado"] is False
    assert planta["ultima_medicion"] is None

    lista = client.get("/api/v1/plantas", headers=headers)
    assert lista.status_code == 200
    assert {item["id"] for item in lista.get_json()} == {1, planta["id"]}

    detalle = client.get(f"/api/v1/plantas/{planta['id']}", headers=headers)
    assert detalle.status_code == 200
    assert detalle.get_json()["id"] == planta["id"]

    borrada = client.delete(f"/api/v1/plantas/{planta['id']}", headers=headers)
    assert borrada.status_code == 200
    assert client.get(f"/api/v1/plantas/{planta['id']}", headers=headers).status_code == 404
    assert [item["id"] for item in client.get("/api/v1/plantas", headers=headers).get_json()] == [1]


def test_borrar_planta_elimina_mediciones_y_valores_asociados(client):
    enviar(client, NORMAL)
    headers = autenticar(client)

    respuesta = client.delete("/api/v1/plantas/1", headers=headers)

    assert respuesta.status_code == 200
    with client.application.app_context():
        from infraestructura.persistencia.sql.modelos import ValorMedicionModelo

        assert MedicionModelo.query.count() == 0
        assert ValorMedicionModelo.query.count() == 0


def test_usuario_no_puede_consultar_ni_borrar_planta_ajena(client):
    registro = client.post(
        "/api/v1/usuarios/registro",
        json={"email": "otra@planttech.com", "contrasena": "contrasena-segura"},
    )
    assert registro.status_code == 201
    headers = autenticar(client, "otra@planttech.com", "contrasena-segura")

    assert client.get("/api/v1/plantas/1", headers=headers).status_code == 404
    assert client.delete("/api/v1/plantas/1", headers=headers).status_code == 404


def test_crear_planta_rechaza_especie_no_soportada(client):
    headers = autenticar(client)

    respuesta = client.post(
        "/api/v1/plantas",
        json={"especie": "Especie inventada"},
        headers=headers,
    )

    assert respuesta.status_code == 400
    assert respuesta.get_json()["error"] == "ERROR_DE_NEGOCIO"
