import time
import random
import requests

# Configuración
DISPOSITIVO_ID = "ESP32_TEST_001"
TOKEN = "token_secreto_123"
#URL_API = f"http://localhost:5000/api/v1/dispositivos/{DISPOSITIVO_ID}/mediciones"
URL_API = f"https://arqsoftwareproyecto-production.up.railway.app/api/v1/dispositivos/ESP32_TEST_001/mediciones"
INTERVALO_SEGUNDOS = 5

def generar_datos_normales():
    return {"temperatura": round(random.uniform(20.0, 25.0), 1), "humedad": round(random.uniform(50.0, 70.0), 1), "luz": random.randint(800, 1000)}

def generar_datos_anomalos():
    return {"temperatura": round(random.uniform(35.0, 45.0), 1), "humedad": 10.0, "luz": 9000} # Valores extremos

def generar_datos_invalidos():
    return {"temperatura": "texto_roto", "humedad": None} # Provocará fallo en el validador_request

def ejecutar_simulacion():
    headers = {"X-Device-Token": TOKEN, "Content-Type": "application/json"}
    escenarios = [generar_datos_normales, generar_datos_anomalos, generar_datos_invalidos]
    pesos = [70, 20, 10] # 70% normal, 20% anomalos, 10% invalidos

    print(f"--- Iniciando Simulador ESP32 ({DISPOSITIVO_ID}) ---")
    while True:
        generador = random.choices(escenarios, weights=pesos)[0]
        payload = {"valores": generador()}
        
        print(f"Enviando: {payload}")
        try:
            respuesta = requests.post(URL_API, json=payload, headers=headers)
            print(f"Respuesta Backend [{respuesta.status_code}]: {respuesta.text}\n")
        except requests.exceptions.ConnectionError:
            print("Error: No se pudo conectar al servidor. ¿Está Flask corriendo?\n")
            
        time.sleep(INTERVALO_SEGUNDOS)

if __name__ == '__main__':
    ejecutar_simulacion()