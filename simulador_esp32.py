import time
import random
import requests

# Configuración
DISPOSITIVO_ID = "ESP32_TEST_001"
TOKEN = "token_secreto_123"
URL_API = f"http://localhost:5000/api/v1/dispositivos/{DISPOSITIVO_ID}/mediciones"
INTERVALO_SEGUNDOS = 5

# Rangos óptimos de la especie "Cinta" (ver backend/seed.py):
#   temperatura 18-24 °C | humedad 40-60 % | luz 500-1000 lux


def generar_datos_normales():
    # Dentro del rango óptimo -> 201 SALUDABLE
    return {"temperatura": round(random.uniform(19.0, 23.0), 1), "humedad": round(random.uniform(45.0, 58.0), 1), "luz": random.randint(600, 950)}


def generar_datos_anomalos():
    # Fuera del óptimo pero físicamente posibles -> 201 CRITICO
    return {"temperatura": round(random.uniform(35.0, 45.0), 1), "humedad": 10.0, "luz": 9000}


def generar_datos_invalidos():
    # Sensor defectuoso: texto o null -> 400 VALOR_NO_NUMERICO
    return random.choice([
        {"temperatura": "texto_roto", "humedad": 50.0, "luz": 800},
        {"temperatura": 22.0, "humedad": None, "luz": 800},
    ])


def generar_datos_imposibles():
    # Lectura físicamente imposible -> 400 VALOR_FUERA_DE_RANGO_FISICO
    return {"temperatura": 9999.0, "humedad": 50.0, "luz": 800}


def ejecutar_simulacion():
    headers = {"X-Device-Token": TOKEN, "Content-Type": "application/json"}
    escenarios = [generar_datos_normales, generar_datos_anomalos, generar_datos_invalidos, generar_datos_imposibles]
    pesos = [65, 20, 10, 5]

    print(f"--- Iniciando Simulador ESP32 ({DISPOSITIVO_ID}) ---")
    while True:
        generador = random.choices(escenarios, weights=pesos)[0]
        payload = {"valores": generador()}

        print(f"Enviando [{generador.__name__}]: {payload}")
        try:
            respuesta = requests.post(URL_API, json=payload, headers=headers, timeout=10)
            print(f"Respuesta Backend [{respuesta.status_code}]: {respuesta.text}\n")
        except requests.exceptions.ConnectionError:
            print("Error: No se pudo conectar al servidor. ¿Está Flask corriendo?\n")

        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == '__main__':
    ejecutar_simulacion()
