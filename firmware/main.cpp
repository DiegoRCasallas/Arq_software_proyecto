// Matera inteligente - firmware ESP32 (WROOM-32) para el backend PlantTech.
// Montaje actual: OLED SSD1306 (D21/D22), DHT22 (D4) y modulo LDR analogico (D34).
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiManager.h>
#include <Wire.h>

// ---------- CONFIGURACION ----------
// Cambia esta IP por la de tu PC (en Ubuntu: hostname -I) o tu URL de Railway
static const char *API_BASE_URL = "http://172.20.10.2:5000";
static const char *DEVICE_ID = "ESP32_TEST_001";
static const char *DEVICE_TOKEN = "token_secreto_123";
static const uint32_t INTERVALO_MS = 10000;

// Pines (coinciden con tu montaje en protoboard)
#define PIN_SDA 21
#define PIN_SCL 22
#define PIN_DHT 4
#define DHT_TYPE DHT22
#define PIN_LDR 34 // ADC1 (funciona con WiFi activo)

// Calibracion del modulo LDR:
// Si al tapar el sensor el valor en Monitor Serial SUBE, cambia LDR_INVERTIDO a 1.
#define LDR_INVERTIDO 1
#define LDR_LUX_MAX 2000.0f // Rango aproximado de luz interior (0 a 2000 lux)

#define OLED_W 128
#define OLED_H 64
#define OLED_ADDR 0x3C // algunos modulos usan 0x3D

Adafruit_SSD1306 oled(OLED_W, OLED_H, &Wire, -1);
DHT dht(PIN_DHT, DHT_TYPE);

struct Respuesta {
  int http = 0;
  String estado;  // estado_general o codigo de error
  String t, h, l; // BAJO / OPTIMO / ALTO / REPOSO_NOCTURNO
};

static String abrev(const String &s) {
  if (s == "OPTIMO")
    return "OK";
  if (s == "REPOSO_NOCTURNO")
    return "NOCHE";
  return s; // BAJO / ALTO
}

void pantalla(const String &linea1, const String &grande, const String &l3 = "",
              const String &l4 = "", const String &l5 = "") {
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);
  oled.setTextSize(1);
  oled.setCursor(0, 0);
  oled.print(linea1);
  oled.setTextSize(2);
  oled.setCursor(0, 11);
  oled.print(grande);
  oled.setTextSize(1);
  oled.setCursor(0, 34);
  oled.print(l3);
  oled.setCursor(0, 44);
  oled.print(l4);
  oled.setCursor(0, 54);
  oled.print(l5);
  oled.display();
}

float leerLuzLux(int &rawPromedio) {
  long suma = 0;
  for (int i = 0; i < 10; i++) {
    suma += analogRead(PIN_LDR);
    delay(5);
  }
  rawPromedio = (int)(suma / 10);

  int efectivo = LDR_INVERTIDO ? (4095 - rawPromedio) : rawPromedio;
  float lux = (efectivo / 4095.0f) * LDR_LUX_MAX;
  return constrain(lux, 0.0f, LDR_LUX_MAX);
}

Respuesta enviar(bool hayTemperatura, float temperatura, bool hayHumedad,
                 float humedad, bool hayLuz, float luz) {
  Respuesta r;
  JsonDocument doc;
  if (hayTemperatura)
    doc["valores"]["temperatura"] = temperatura;
  if (hayHumedad)
    doc["valores"]["humedad"] = humedad;
  if (hayLuz)
    doc["valores"]["luz"] = luz;
  String cuerpo;
  serializeJson(doc, cuerpo);

  String url = String(API_BASE_URL) + "/api/v1/dispositivos/" + DEVICE_ID +
               "/mediciones";
  HTTPClient http;
  WiFiClient plano;
  WiFiClientSecure seguro;
  bool ok;
  if (url.startsWith("https")) {
    seguro.setInsecure();
    ok = http.begin(seguro, url);
  } else {
    ok = http.begin(plano, url);
  }
  if (!ok) {
    r.estado = "URL_INVALIDA";
    return r;
  }

  http.setTimeout(15000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  r.http = http.POST(cuerpo);
  if (r.http > 0) {
    String payload = http.getString();
    JsonDocument res;
    if (!deserializeJson(res, payload)) {
      if (r.http == 201) {
        r.estado = res["estado_general"] | "?";
        r.t = res["detalle_parametros"]["temperatura"] | "";
        r.h = res["detalle_parametros"]["humedad"] | "";
        r.l = res["detalle_parametros"]["luz"] | "";
      } else {
        r.estado = res["error"] | "ERROR";
      }
    }
    Serial.printf("HTTP %d -> %s\n", r.http, payload.c_str());
  } else {
    r.estado = "SIN_CONEXION";
    Serial.printf("Error HTTP: %s\n",
                  HTTPClient::errorToString(r.http).c_str());
  }
  http.end();
  return r;
}

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  if (!oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("OLED no encontrado (revisa direccion 0x3C/0x3D y cableado)");
  }
  pantalla("Matera inteligente", "Iniciando");

  dht.begin();
  analogReadResolution(12);
  pinMode(PIN_LDR, INPUT);

  pantalla("WiFi", "Conectando", "Si falla: Matera-Setup", "192.168.4.1");
  WiFiManager wm;
  // autoConnect recuerda tu WiFi; solo abre el portal si no tiene red guardada
  if (!wm.autoConnect("Matera-Setup")) {
    ESP.restart();
  }
  pantalla("WiFi OK", WiFi.localIP().toString());
  delay(1500);
}

void loop() {
  static uint32_t ultimo = 0;
  if (millis() - ultimo < INTERVALO_MS && ultimo != 0)
    return;
  ultimo = millis();

  if (WiFi.status() != WL_CONNECTED) {
    pantalla("Sin WiFi", "Reconectando");
    WiFi.reconnect();
    return;
  }

  float t = dht.readTemperature();
  float h = dht.readHumidity(); // Usando DHT22 mientras se integra sensor de suelo
  bool hayTemperatura = !isnan(t);
  bool hayHumedad = !isnan(h);

  int ldrRaw = 0;
  float lux = leerLuzLux(ldrRaw);
  bool hayLuz = true;

  if (!hayTemperatura && !hayHumedad && !hayLuz) {
    pantalla("Error de sensores", "SIN DATOS");
    return;
  }

  Serial.printf("T=%s H=%s L=%.0f (raw=%d)\n",
                hayTemperatura ? String(t, 1).c_str() : "NC",
                hayHumedad ? String(h, 1).c_str() : "NC",
                lux, ldrRaw);

  Respuesta r = enviar(hayTemperatura, t, hayHumedad, h, hayLuz, lux);

  String l3 = hayTemperatura ? "T " + String(t, 1) + "C " + abrev(r.t)
                             : "T desconectado";
  String l4 = hayHumedad ? "H " + String(h, 0) + "% " + abrev(r.h)
                         : "H desconectado";
  String l5 = "L " + String(lux, 0) + "lx " + abrev(r.l);
  String cab = "HTTP " + String(r.http);

  pantalla(cab, r.http == 201 ? r.estado : "ERROR", l3, l4,
           r.http == 201 ? l5 : r.estado);
}
