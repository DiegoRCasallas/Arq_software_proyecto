from datetime import datetime, timedelta

from infraestructura.persistencia.sql.modelos import (
    PlantaModelo,
    SesionVinculacionModelo,
    db,
)


DISPOSITIVO_ID = "a" * 24
CODIGO = "b" * 32
TOKEN_DISPOSITIVO = "c" * 64


def autenticar(client):
    respuesta = client.post(
        "/api/v1/usuarios/login",
        json={"email": "prueba@planttech.com", "contrasena": "12345"},
    )
    return {"Authorization": f"Bearer {respuesta.get_json()['token']}"}


def preparar_desde_dispositivo(
    client, codigo=CODIGO, token=TOKEN_DISPOSITIVO
):
    return client.post(
        f"/api/v1/dispositivos/{DISPOSITIVO_ID}/vinculacion/preparar",
        headers={
            "X-Pairing-Code": codigo,
            "X-Device-Token": token,
        },
    )


def iniciar_vinculacion(client, headers, codigo=CODIGO):
    preparada = preparar_desde_dispositivo(client, codigo)
    assert preparada.status_code == 200
    return client.post(
        "/api/v1/plantas/1/dispositivo",
        json={
            "dispositivo_id": DISPOSITIVO_ID,
            "codigo_vinculacion": codigo,
        },
        headers=headers,
    )


def confirmar_desde_dispositivo(
    client, codigo=CODIGO, token=TOKEN_DISPOSITIVO, aprobar=False
):
    headers = {
        "X-Pairing-Code": codigo,
        "X-Device-Token": token,
    }
    if aprobar:
        headers["X-Pairing-Approval"] = "confirm"
    return client.post(
        f"/api/v1/dispositivos/{DISPOSITIVO_ID}/vinculacion/confirmar",
        headers=headers,
    )


def test_vinculacion_qr_requiere_solicitud_de_usuario_y_confirmacion_del_esp32(
    app, client
):
    headers = autenticar(client)
    assert preparar_desde_dispositivo(client).status_code == 200
    espera = confirmar_desde_dispositivo(client)
    assert espera.status_code == 202
    assert espera.get_json() == {"estado": "esperando"}

    solicitud = client.post(
        "/api/v1/plantas/1/dispositivo",
        json={
            "dispositivo_id": DISPOSITIVO_ID,
            "codigo_vinculacion": CODIGO,
        },
        headers=headers,
    )

    assert solicitud.status_code == 202
    sesion_id = solicitud.get_json()["sesion_id"]
    assert client.get(
        f"/api/v1/plantas/1/dispositivo/vinculaciones/{sesion_id}",
        headers=headers,
    ).get_json() == {"estado": "pendiente"}

    solicitud_fisica = confirmar_desde_dispositivo(client)
    assert solicitud_fisica.status_code == 202
    assert solicitud_fisica.get_json() == {"estado": "solicitada"}
    with app.app_context():
        planta = db.session.get(PlantaModelo, 1)
        assert planta.dispositivo_id == "ESP32_TEST_001"

    confirmacion = confirmar_desde_dispositivo(client, aprobar=True)
    assert confirmacion.status_code == 200
    assert confirmacion.get_json() == {"estado": "completada"}

    estado = client.get(
        f"/api/v1/plantas/1/dispositivo/vinculaciones/{sesion_id}",
        headers=headers,
    )
    assert estado.get_json() == {"estado": "completada"}

    with app.app_context():
        planta = db.session.get(PlantaModelo, 1)
        sesion = db.session.get(SesionVinculacionModelo, sesion_id)
        assert planta.dispositivo_id == DISPOSITIVO_ID
        assert planta.token_dispositivo_hash != TOKEN_DISPOSITIVO
        assert sesion.codigo_hash != CODIGO
        assert sesion.token_dispositivo_hash != TOKEN_DISPOSITIVO
        assert sesion.completada_en is not None

    repetida = confirmar_desde_dispositivo(client)
    assert repetida.status_code == 200

    medicion = client.post(
        f"/api/v1/dispositivos/{DISPOSITIVO_ID}/mediciones",
        json={"valores": {"temperatura": 22}},
        headers={"X-Device-Token": TOKEN_DISPOSITIVO},
    )
    assert medicion.status_code == 201


def test_preparar_es_idempotente_y_rechaza_credencial_de_otro_dispositivo(client):
    primera = preparar_desde_dispositivo(client)
    repetida = preparar_desde_dispositivo(client)

    assert primera.status_code == repetida.status_code == 200
    assert primera.get_json() == repetida.get_json()

    token_ajeno = "d" * 64
    secuestro = preparar_desde_dispositivo(client, token=token_ajeno)
    confirmar_ajeno = confirmar_desde_dispositivo(client, token=token_ajeno)
    confirmar_dispositivo = confirmar_desde_dispositivo(client)

    assert secuestro.status_code == 409
    assert confirmar_ajeno.status_code == 401
    assert confirmar_dispositivo.status_code == 202


def test_codigo_incorrecto_no_completa_la_vinculacion(client):
    headers = autenticar(client)
    assert iniciar_vinculacion(client, headers).status_code == 202

    respuesta = confirmar_desde_dispositivo(client, codigo="d" * 32)

    assert respuesta.status_code == 202
    assert respuesta.get_json() == {"estado": "esperando"}


def test_solicitud_requiere_jwt_y_codigo_temporal(client):
    preparada = preparar_desde_dispositivo(client)
    assert preparada.status_code == 200

    sin_jwt = client.post(
        "/api/v1/plantas/1/dispositivo",
        json={
            "dispositivo_id": DISPOSITIVO_ID,
            "codigo_vinculacion": CODIGO,
        },
    )
    assert sin_jwt.status_code == 401

    headers = autenticar(client)
    respuesta = client.post(
        "/api/v1/plantas/1/dispositivo",
        json={"dispositivo_id": DISPOSITIVO_ID, "token": TOKEN_DISPOSITIVO},
        headers=headers,
    )
    assert respuesta.status_code == 400


def test_usuario_ajeno_no_puede_consultar_ni_cancelar_sesion(client):
    propietario = autenticar(client)
    solicitud = iniciar_vinculacion(client, propietario)
    sesion_id = solicitud.get_json()["sesion_id"]

    client.post(
        "/api/v1/usuarios/registro",
        json={"email": "otra@planttech.com", "contrasena": "contrasena-segura"},
    )
    otro_usuario = client.post(
        "/api/v1/usuarios/login",
        json={"email": "otra@planttech.com", "contrasena": "contrasena-segura"},
    )
    headers_ajenos = {"Authorization": f"Bearer {otro_usuario.get_json()['token']}"}

    estado = client.get(
        f"/api/v1/plantas/1/dispositivo/vinculaciones/{sesion_id}",
        headers=headers_ajenos,
    )
    cancelar = client.delete(
        f"/api/v1/plantas/1/dispositivo/vinculaciones/{sesion_id}",
        headers=headers_ajenos,
    )
    assert estado.status_code == cancelar.status_code == 404


def test_solo_la_primera_cuenta_puede_reclamar_el_codigo_activo(client):
    propietario = autenticar(client)
    solicitud = iniciar_vinculacion(client, propietario)
    sesion_id = solicitud.get_json()["sesion_id"]

    client.post(
        "/api/v1/usuarios/registro",
        json={"email": "otra@planttech.com", "contrasena": "contrasena-segura"},
    )
    otro_usuario = client.post(
        "/api/v1/usuarios/login",
        json={"email": "otra@planttech.com", "contrasena": "contrasena-segura"},
    )
    headers_ajenos = {"Authorization": f"Bearer {otro_usuario.get_json()['token']}"}
    otra_planta = client.post(
        "/api/v1/plantas",
        json={"especie": "Cinta"},
        headers=headers_ajenos,
    )
    intento = client.post(
        f"/api/v1/plantas/{otra_planta.get_json()['id']}/dispositivo",
        json={
            "dispositivo_id": DISPOSITIVO_ID,
            "codigo_vinculacion": CODIGO,
        },
        headers=headers_ajenos,
    )

    assert intento.status_code == 400
    assert confirmar_desde_dispositivo(client, aprobar=True).status_code == 200
    assert client.get(
        f"/api/v1/plantas/1/dispositivo/vinculaciones/{sesion_id}",
        headers=propietario,
    ).get_json() == {"estado": "completada"}


def test_cancelar_sesion_invalida_el_codigo(app, client):
    headers = autenticar(client)
    solicitud = iniciar_vinculacion(client, headers)
    sesion_id = solicitud.get_json()["sesion_id"]

    cancelada = client.delete(
        f"/api/v1/plantas/1/dispositivo/vinculaciones/{sesion_id}",
        headers=headers,
    )
    confirmacion = confirmar_desde_dispositivo(client)

    assert cancelada.status_code == 200
    assert confirmacion.status_code == 410
    with app.app_context():
        planta = db.session.get(PlantaModelo, 1)
        assert planta.dispositivo_id == "ESP32_TEST_001"


def test_eliminar_planta_conserva_la_credencial_del_dispositivo(app, client):
    headers = autenticar(client)
    solicitud = iniciar_vinculacion(client, headers)
    sesion_id = solicitud.get_json()["sesion_id"]

    eliminada = client.delete("/api/v1/plantas/1", headers=headers)
    intento_con_token_ajeno = preparar_desde_dispositivo(
        client, codigo="d" * 32, token="e" * 64
    )

    assert eliminada.status_code == 200
    assert intento_con_token_ajeno.status_code == 409
    with app.app_context():
        sesion = db.session.get(SesionVinculacionModelo, sesion_id)
        assert sesion.token_dispositivo_hash
        assert sesion.usuario_id is None
        assert sesion.planta_id is None
        assert sesion.expira_en <= datetime.utcnow()


def test_sesion_expirada_no_puede_vincular_el_dispositivo(app, client):
    headers = autenticar(client)
    solicitud = iniciar_vinculacion(client, headers)
    sesion_id = solicitud.get_json()["sesion_id"]
    with app.app_context():
        sesion = db.session.get(SesionVinculacionModelo, sesion_id)
        sesion.expira_en = datetime.utcnow() - timedelta(seconds=1)
        db.session.commit()

    respuesta = confirmar_desde_dispositivo(client)

    assert respuesta.status_code == 410
    with app.app_context():
        planta = db.session.get(PlantaModelo, 1)
        assert planta.dispositivo_id == "ESP32_TEST_001"
