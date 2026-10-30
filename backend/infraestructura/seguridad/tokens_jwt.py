import jwt
import datetime
import os
from typing import Dict, Any

class TokensJWT:
    def __init__(self):
        # En producción (Railway), JWT_SECRET se lee de las variables de entorno
        self.secreto = os.getenv('JWT_SECRET', 'clave_secreta_desarrollo_123')

    def generar_token(self, usuario_id: int) -> str:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'iat': datetime.datetime.utcnow(),
            'sub': usuario_id
        }
        return jwt.encode(payload, self.secreto, algorithm='HS256')

    def validar_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.secreto, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise ValueError("TOKEN_EXPIRADO")
        except jwt.InvalidTokenError:
            raise ValueError("TOKEN_INVALIDO")