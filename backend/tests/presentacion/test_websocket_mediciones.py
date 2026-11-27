import json

from presentacion.ws.mediciones import GestorConexiones


class WebSocketFalso:
    def __init__(self):
        self.mensajes = []

    def send(self, mensaje):
        self.mensajes.append(mensaje)


def test_emite_medicion_solo_a_las_conexiones_del_usuario_destinatario():
    gestor = GestorConexiones()
    conexion_destino = WebSocketFalso()
    conexion_ajena = WebSocketFalso()
    gestor.registrar(1, conexion_destino)
    gestor.registrar(2, conexion_ajena)
    evento = {"tipo": "medicion", "planta_id": 7}

    gestor.emitir(1, evento)

    assert [json.loads(mensaje) for mensaje in conexion_destino.mensajes] == [evento]
    assert conexion_ajena.mensajes == []
