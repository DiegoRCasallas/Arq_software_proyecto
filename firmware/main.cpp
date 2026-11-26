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
#include <memory>

// ---------- CONFIGURACION ----------
// URL del backend en Railway (HTTPS, funciona en cualquier red)
static const char *API_HOST = "arqsoftwareproyecto-production.up.railway.app";
static const char *API_BASE_URL = "https://arqsoftwareproyecto-production.up.railway.app";
static const char *DEVICE_ID = "ESP32_TEST_001";
static const char *DEVICE_TOKEN = "token_secreto_123";
static const uint32_t INTERVALO_MS = 10000;
static const uint32_t INTERVALO_MUESTREO_MS = 2000;

// WiFi: botón de reset de credenciales
// GPIO 0 = botón BOOT del ESP32-WROOM (ya viene en el board, sin cableado extra)
// Mantén presionado al encender → borra la red guardada y abre el portal de config.
#define PIN_RESET_WIFI 0
#define RESET_HOLD_MS  3000   // tiempo que hay que mantenerlo (ms)
#define PORTAL_TIMEOUT 180    // segundos que el portal estará abierto si no conecta

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

struct AcumuladorMediciones {
  float sumaTemperatura = 0;
  float sumaHumedad = 0;
  float sumaLuz = 0;
  uint16_t muestrasTemperatura = 0;
  uint16_t muestrasHumedad = 0;
  uint16_t muestrasLuz = 0;
};

static uint32_t inicioPeriodo = 0;
static uint32_t ultimaMuestra = 0;
static AcumuladorMediciones acumulador;
static Respuesta ultimaRespuesta;

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
  oled.setTextWrap(false);
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

static void formatearLineasSensores(bool hayTemperatura, float temperatura,
                                    bool hayHumedad, float humedad,
                                    bool hayLuz, float luz,
                                    const Respuesta &resp,
                                    String &l3, String &l4, String &l5) {
  bool ok = resp.http == 201;
  l3 = hayTemperatura
           ? "T " + String(temperatura, 1) + "C" + (ok ? " " + abrev(resp.t) : "")
           : "T desconectado";
  l4 = hayHumedad
           ? "H " + String(humedad, 0) + "%" + (ok ? " " + abrev(resp.h) : "")
           : "H desconectado";
  l5 = hayLuz
           ? "L " + String(luz, 0) + "lx" + (ok ? " " + abrev(resp.l) : "")
           : "L desconectado";
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
  std::unique_ptr<WiFiClient> plano;
  std::unique_ptr<WiFiClientSecure> seguro;
  HTTPClient http;
  bool ok;
  if (url.startsWith("https")) {
    seguro.reset(new WiFiClientSecure());
    seguro->setInsecure();
    ok = http.begin(*seguro, url);
  } else {
    plano.reset(new WiFiClient());
    ok = http.begin(*plano, url);
  }
  if (!ok) {
    r.estado = "URL_INVALIDA";
    return r;
  }

  http.setTimeout(15000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", DEVICE_TOKEN);

  Serial.println("Enviando POST...");
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
    IPAddress ip;
    bool dnsOk = WiFi.hostByName(API_HOST, ip);
    bool ipValida = dnsOk && ip != IPAddress(0, 0, 0, 0);
    Serial.printf("Error HTTP (%d): %s | heap=%lu | rssi=%d | dns=%s (%s)\n",
                  r.http, HTTPClient::errorToString(r.http).c_str(),
                  static_cast<unsigned long>(ESP.getFreeHeap()), WiFi.RSSI(),
                  ipValida ? "OK" : "FAIL", ip.toString().c_str());
    if (seguro) {
      char errBuf[128] = {0};
      int tlsErr = seguro->lastError(errBuf, sizeof(errBuf));
      if (tlsErr != 0) {
        Serial.printf("TLS error (%d): %s\n", tlsErr, errBuf);
      }
    }

    if (ipValida) {
      WiFiClient tcpProbe;
      tcpProbe.setConnectionTimeout(5000);
      bool tcpOk = tcpProbe.connect(ip, 443, 5000);
      Serial.printf("Diagnostico TCP 443 a %s: %s\n", ip.toString().c_str(),
                    tcpOk ? "OK" : "FALLO");
      tcpProbe.stop();

      if (tcpOk) {
        WiFiClientSecure tlsProbe;
        tlsProbe.setInsecure();
        tlsProbe.setHandshakeTimeout(5);
        bool tlsOk = tlsProbe.connect(API_HOST, 443, 5000);
        if (tlsOk) {
          Serial.println("Diagnostico TLS: OK");
        } else {
          char errBuf[128] = {0};
          int tlsErr = tlsProbe.lastError(errBuf, sizeof(errBuf));
          Serial.printf("Diagnostico TLS: FALLO (%d): %s\n", tlsErr, errBuf);
        }
        tlsProbe.stop();
      }
    } else {
      Serial.println("Diagnostico TCP 443: OMITIDO (DNS sin IP valida)");
    }
  }
  http.end();
  return r;
}

// Detecta si el botón BOOT se mantiene presionado al encender.
// Retorna true si se sostuvo >= RESET_HOLD_MS ms.
static bool botonResetPresionado() {
  pinMode(PIN_RESET_WIFI, INPUT_PULLUP);
  if (digitalRead(PIN_RESET_WIFI) != LOW)
    return false; // no está presionado, salir rápido

  // Está presionado: esperar el tiempo mínimo con feedback visual
  uint32_t inicio = millis();
  while (digitalRead(PIN_RESET_WIFI) == LOW) {
    uint32_t transcurrido = millis() - inicio;
    if (transcurrido >= RESET_HOLD_MS)
      return true;
    // Barra de progreso en OLED
    int porcentaje = (transcurrido * 100) / RESET_HOLD_MS;
    oled.clearDisplay();
    oled.setTextSize(1);
    oled.setTextColor(SSD1306_WHITE);
    oled.setCursor(0, 0);
    oled.print("Suelta para cancelar");
    oled.setCursor(0, 16);
    oled.print("Borrando WiFi...");
    oled.drawRect(0, 40, 128, 12, SSD1306_WHITE);
    oled.fillRect(2, 42, (124 * porcentaje) / 100, 8, SSD1306_WHITE);
    oled.display();
    delay(50);
  }
  return false; // soltó antes de tiempo
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

  WiFiManager wm;

  // --- Reset de credenciales WiFi ---
  // Mantén el botón BOOT (GPIO 0) al encender 3 s para borrar la red guardada.
  if (botonResetPresionado()) {
    Serial.println("Reset WiFi: borrando credenciales guardadas");
    wm.resetSettings();
    pantalla("WiFi Reset", "Credenciales", "borradas", "Abriendo portal...");
    delay(1500);
  }

  // --- Conexión WiFi con portal de respaldo ---
  // Si hay red guardada → conecta directamente (sin abrir portal).
  // Si no hay red ó falla en PORTAL_TIMEOUT s → abre "Matera-Setup" en 192.168.4.1
  // y espera configuración. Si nadie configura en ese tiempo → reinicia.
  wm.setConnectTimeout(30);            // tiempo máximo buscando la red guardada (s)
  wm.setConfigPortalTimeout(PORTAL_TIMEOUT); // tiempo que el portal permanece abierto (s)
  pantalla("WiFi", "Conectando...", "BOOT 3s = cambiar red", "192.168.4.1");

  if (!wm.autoConnect("Matera-Setup")) {
    // Timeout del portal agotado → reiniciar e intentar de nuevo
    Serial.println("Portal de config cerrado sin configurar. Reiniciando...");
    pantalla("Sin WiFi", "Reiniciando", "en 3 s...");
    delay(3000);
    ESP.restart();
  }

  WiFi.setSleep(false);
  pantalla("WiFi OK", WiFi.localIP().toString());
  delay(1500);

  uint32_t ahora = millis();
  inicioPeriodo = ahora;
  ultimaMuestra = ahora - INTERVALO_MUESTREO_MS;
}

void loop() {
  uint32_t ahora = millis();

  if (ahora - ultimaMuestra >= INTERVALO_MUESTREO_MS) {
    float temperatura = dht.readTemperature();
    float humedad = dht.readHumidity(); // DHT22 requiere al menos 2 s entre lecturas.
    int ldrRaw = 0;
    float luz = leerLuzLux(ldrRaw);
    ultimaMuestra = millis();

    bool hayTemperatura = !isnan(temperatura);
    bool hayHumedad = !isnan(humedad);
    if (hayTemperatura) {
      acumulador.sumaTemperatura += temperatura;
      acumulador.muestrasTemperatura++;
    }
    if (hayHumedad) {
      acumulador.sumaHumedad += humedad;
      acumulador.muestrasHumedad++;
    }
    acumulador.sumaLuz += luz;
    acumulador.muestrasLuz++;

    Serial.printf("Muestra T=%s H=%s L=%.1f (raw=%d)\n",
                  hayTemperatura ? String(temperatura, 1).c_str() : "NC",
                  hayHumedad ? String(humedad, 1).c_str() : "NC",
                  luz, ldrRaw);

    if (millis() - inicioPeriodo < INTERVALO_MS) {
      String l3, l4, l5;
      formatearLineasSensores(hayTemperatura, temperatura, hayHumedad, humedad,
                              true, luz, ultimaRespuesta, l3, l4, l5);
      String cab;
      String grande;
      if (ultimaRespuesta.http == 201) {
        cab = "M" + String(acumulador.muestrasLuz) + " | HTTP 201";
        grande = ultimaRespuesta.estado;
      } else if (ultimaRespuesta.http != 0) {
        cab = "M" + String(acumulador.muestrasLuz) + " | HTTP " +
              String(ultimaRespuesta.http);
        grande = "ERROR";
      } else {
        cab = "Muestra " + String(acumulador.muestrasLuz) + " (10s)";
        grande = "MIDIENDO";
      }
      pantalla(cab, grande, l3, l4, l5);
    }
  }

  if (millis() - inicioPeriodo >= INTERVALO_MS) {
    bool hayTemperatura = acumulador.muestrasTemperatura > 0;
    bool hayHumedad = acumulador.muestrasHumedad > 0;
    bool hayLuz = acumulador.muestrasLuz > 0;
    float temperatura = hayTemperatura
                            ? acumulador.sumaTemperatura /
                                  acumulador.muestrasTemperatura
                            : 0;
    float humedad = hayHumedad
                        ? acumulador.sumaHumedad / acumulador.muestrasHumedad
                        : 0;
    float luz = hayLuz ? acumulador.sumaLuz / acumulador.muestrasLuz : 0;

    Serial.printf("Promedio de %u muestras: T=%s H=%s L=%.1f\n",
                  acumulador.muestrasLuz,
                  hayTemperatura ? String(temperatura, 1).c_str() : "NC",
                  hayHumedad ? String(humedad, 1).c_str() : "NC", luz);

    if (WiFi.status() != WL_CONNECTED) {
      pantalla("Sin WiFi", "Reconectando");
      WiFi.reconnect();
    } else if (hayTemperatura || hayHumedad || hayLuz) {
      {
        String l3, l4, l5;
        formatearLineasSensores(hayTemperatura, temperatura, hayHumedad, humedad,
                                hayLuz, luz, ultimaRespuesta, l3, l4, l5);
        pantalla("Enviando (" + String(acumulador.muestrasLuz) + "m)",
                 "ENVIANDO", l3, l4, l5);
      }

      Respuesta r = enviar(hayTemperatura, temperatura, hayHumedad, humedad,
                           hayLuz, luz);
      ultimaRespuesta = r;

      {
        String l3, l4, l5;
        formatearLineasSensores(hayTemperatura, temperatura, hayHumedad, humedad,
                                hayLuz, luz, r, l3, l4, l5);
        String cab = "HTTP " + String(r.http) + " (" +
                     String(acumulador.muestrasLuz) + "m)";

        pantalla(cab, r.http == 201 ? r.estado : "ERROR", l3, l4,
                 r.http == 201 ? l5 : r.estado);
      }
    } else {
      pantalla("Error de sensores", "SIN DATOS");
    }

    acumulador = {};
    inicioPeriodo = millis();
    ultimaMuestra = inicioPeriodo;
  }

  delay(10);
}
