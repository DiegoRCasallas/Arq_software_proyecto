// Matera inteligente - firmware ESP32 (WROOM-32) para el backend PlantTech.
// Envia POST /api/v1/dispositivos/<id>/mediciones con
// {"valores":{temperatura,humedad,luz}} y muestra el diagnostico en el OLED
// SSD1306 128x64.
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <ArduinoJson.h>
#include <BH1750.h>
#include <DHT.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiManager.h>
#include <Wire.h>

// ---------- CONFIGURACION ----------
// Local: IP de tu PC en la misma red WiFi (NO "localhost"). Railway:
// https://...
static const char *API_BASE_URL = "http://192.168.78.182:5000";
// static const char* API_BASE_URL =
// "https://arqsoftwareproyecto-production.up.railway.app";
static const char *DEVICE_ID = "ESP32_TEST_001";
static const char *DEVICE_TOKEN = "token_secreto_123";
static const uint32_t INTERVALO_MS = 10000;

// Pines
#define PIN_SDA 21
#define PIN_SCL 22
#define PIN_DHT 4
#define DHT_TYPE DHT22 // cambia a DHT11 si es el azul
#define PIN_SOIL 34    // ADC1 (los ADC2 no funcionan con WiFi activo)

// "humedad" en el backend = humedad del SUSTRATO (RF1).
// 1 = sensor capacitivo de suelo en PIN_SOIL. 0 = usa la humedad del aire del
// DHT (solo para pruebas).
#define HUMEDAD_DESDE_SUELO 1
#define SOIL_RAW_SECO 3200   // lectura al aire (calibrar)
#define SOIL_RAW_HUMEDO 1400 // lectura sumergido en agua (calibrar)

#define OLED_W 128
#define OLED_H 64
#define OLED_ADDR 0x3C // algunos modulos usan 0x3D

Adafruit_SSD1306 oled(OLED_W, OLED_H, &Wire, -1);
DHT dht(PIN_DHT, DHT_TYPE);
BH1750 luxometro;

struct Respuesta {
  int http = 0;
  String estado;  // estado_general o codigo de error
  String t, h, l; // BAJO / OPTIMO / ALTO
};

static String abrev(const String &s) {
  if (s == "OPTIMO")
    return "OK";
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

float leerHumedad(float humedadAireDht) {
#if HUMEDAD_DESDE_SUELO
  int raw = analogRead(PIN_SOIL);
  float pct =
      (float)(SOIL_RAW_SECO - raw) * 100.0f / (SOIL_RAW_SECO - SOIL_RAW_HUMEDO);
  return constrain(pct, 0.0f, 100.0f);
#else
  return humedadAireDht;
#endif
}

Respuesta enviar(float temperatura, float humedad, float luz) {
  Respuesta r;
  JsonDocument doc;
  doc["valores"]["temperatura"] = temperatura;
  doc["valores"]["humedad"] = humedad;
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
    seguro.setInsecure(); // simple para el proyecto; en produccion usar
                          // setCACert()
    ok = http.begin(seguro, url);
  } else {
    ok = http.begin(plano, url);
  }
  if (!ok) {
    r.estado = "URL_INVALIDA";
    return r;
  }

  http.setTimeout(15000); // Railway puede tardar en "despertar"
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
        r.estado = res["error"] | "ERROR"; // p.ej. VALOR_FUERA_DE_RANGO_FISICO
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
    Serial.println(
        "OLED no encontrado (revisa direccion 0x3C/0x3D y cableado)");
  }
  pantalla("Matera inteligente", "Iniciando");

  dht.begin();
  luxometro.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
  analogReadResolution(12);

  pantalla("WiFi", "Configurar red", "AP: Matera-Setup", "192.168.4.1");
  WiFiManager wm;
  wm.resetSettings();
  if (!wm.startConfigPortal("Matera-Setup")) {
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
  float hAire = dht.readHumidity();
  float lux = luxometro.readLightLevel();
  float h = leerHumedad(hAire);

  // El backend rechaza NaN/null (400 VALOR_NO_NUMERICO): no se envia una
  // lectura rota.
  if (isnan(t) || isnan(h) || lux < 0) {
    pantalla("Error de sensor", "REVISAR", isnan(t) ? "DHT sin lectura" : "",
             lux < 0 ? "BH1750 sin lectura" : "");
    return;
  }

  Serial.printf("T=%.1f H=%.1f L=%.0f\n", t, h, lux);
  Respuesta r = enviar(t, h, lux);

  String l3 = "T " + String(t, 1) + "C " + abrev(r.t);
  String l4 = "H " + String(h, 0) + "% " + abrev(r.h);
  String l5 = "L " + String(lux, 0) + "lx " + abrev(r.l);
  String cab = "HTTP " + String(r.http);
  // estado puede ser largo (CRITICO/EN_RIESGO) -> size 2 cabe ~10 caracteres
  pantalla(cab, r.http == 201 ? r.estado : "ERROR", l3, l4,
           r.http == 201 ? l5 : r.estado);
}
