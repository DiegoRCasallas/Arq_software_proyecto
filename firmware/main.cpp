// Matera inteligente - firmware ESP32 (WROOM-32) para el backend PlantTech.
// Montaje actual: OLED SSD1306 (D21/D22), DHT22 (D4) y modulo LDR analogico (D34).
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Arduino.h>
#include <ArduinoJson.h>
#include <DHT.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <qrcode.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <WiFiManager.h>
#include <Wire.h>
#include <esp_system.h>

// ---------- CONFIGURACION ----------
// URL del backend en Railway (HTTPS, funciona en cualquier red)
static const char *API_HOST = "arqsoftwareproyecto-production.up.railway.app";
static const char *API_BASE_URL = "https://arqsoftwareproyecto-production.up.railway.app";
static const uint32_t INTERVALO_MS = 10000;
static const uint32_t INTERVALO_MUESTREO_MS = 2000;
static const uint32_t INTERVALO_VINCULACION_MS = 3000;
static const uint32_t VINCULACION_BUTTON_HOLD_MS = 5000;
static const uint32_t VINCULACION_APPROVAL_HOLD_MS = 2000;

static const char *CERTIFICADO_RAIZ = R"PEM(
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
B5iPNgiV5+3I+1lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
-----END CERTIFICATE-----
)PEM";

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
Preferences preferencias;
static String dispositivoId;
static String tokenDispositivo;
static String codigoVinculacion;
static bool dispositivoVinculado = false;
static bool codigoPreparado = false;
static bool solicitudVinculacionPendiente = false;
static bool aprobacionVinculacionFisica = false;
static bool vinculacionRechazada = false;
static uint32_t ultimaConsultaVinculacion = 0;

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

static void pantalla(const String &linea1, const String &grande,
                     const String &l3 = String(), const String &l4 = String(),
                     const String &l5 = String());

static String generarHexAleatorio(size_t cantidadBytes) {
  static const char HEX[] = "0123456789abcdef";
  String resultado;
  resultado.reserve(cantidadBytes * 2);
  for (size_t i = 0; i < cantidadBytes; ++i) {
    uint8_t valor = static_cast<uint8_t>(esp_random());
    resultado += HEX[valor >> 4];
    resultado += HEX[valor & 0x0F];
  }
  return resultado;
}

static void guardarNuevoCodigoVinculacion() {
  codigoVinculacion = generarHexAleatorio(16);
  if (preferencias.putString("pair_code", codigoVinculacion) == 0) {
    Serial.println("No se pudo guardar el codigo temporal en NVS");
    pantalla("Error NVS", "Reinicia");
    while (true)
      delay(1000);
  }
  codigoPreparado = false;
  solicitudVinculacionPendiente = false;
  aprobacionVinculacionFisica = false;
  vinculacionRechazada = false;
}

static void cargarCredencialesDispositivo() {
  if (!preferencias.begin("planttech", false)) {
    Serial.println("No se pudo abrir la memoria NVS");
    pantalla("Error NVS", "Reinicia");
    while (true)
      delay(1000);
  }

  dispositivoId = preferencias.getString("device_id", "");
  tokenDispositivo = preferencias.getString("device_token", "");
  dispositivoVinculado = preferencias.getBool("paired", false);

  if (dispositivoId.length() != 24 || tokenDispositivo.length() != 64) {
    dispositivoId = generarHexAleatorio(12);
    tokenDispositivo = generarHexAleatorio(32);
    dispositivoVinculado = false;
    if (preferencias.putString("device_id", dispositivoId) == 0 ||
        preferencias.putString("device_token", tokenDispositivo) == 0 ||
        !preferencias.putBool("paired", false)) {
      Serial.println("No se pudieron guardar las credenciales del dispositivo");
      pantalla("Error NVS", "Reinicia");
      while (true)
        delay(1000);
    }
    preferencias.remove("pair_code");
  }

  if (!dispositivoVinculado) {
    codigoVinculacion = preferencias.getString("pair_code", "");
    if (codigoVinculacion.length() != 32) {
      guardarNuevoCodigoVinculacion();
    }
  }
}

static void mostrarQRVinculacion() {
  String contenido = "PT1:" + dispositivoId + ":" + codigoVinculacion;
  QRCode codigoQR;
  uint8_t bufferQR[256];
  int8_t resultado = qrcode_initText(
      &codigoQR, bufferQR, 5, ECC_MEDIUM, contenido.c_str());
  if (resultado < 0 || codigoQR.size + 8 > OLED_H) {
    pantalla("Error QR", "Reinicia");
    return;
  }

  const int borde = 4;
  const int lado = codigoQR.size + borde * 2;
  const int inicioX = (OLED_W - lado) / 2;
  const int inicioY = (OLED_H - lado) / 2;
  oled.clearDisplay();
  oled.fillRect(inicioX, inicioY, lado, lado, SSD1306_WHITE);
  for (uint8_t y = 0; y < codigoQR.size; ++y) {
    for (uint8_t x = 0; x < codigoQR.size; ++x) {
      if (qrcode_getModule(&codigoQR, x, y)) {
        oled.drawPixel(inicioX + borde + x, inicioY + borde + y,
                       SSD1306_BLACK);
      }
    }
  }
  oled.display();
}

static bool abrirHttpSeguro(HTTPClient &http, WiFiClientSecure &seguro,
                            const String &url) {
  if (!url.startsWith("https://")) {
    return false;
  }
  seguro.setCACert(CERTIFICADO_RAIZ);
  return http.begin(seguro, url);
}

static bool marcarDispositivoVinculado() {
  if (!preferencias.putBool("paired", true)) {
    Serial.println("No se pudo guardar el estado de vinculacion");
    pantalla("Error NVS", "Reinicia");
    return false;
  }
  dispositivoVinculado = true;
  codigoPreparado = false;
  solicitudVinculacionPendiente = false;
  aprobacionVinculacionFisica = false;
  preferencias.remove("pair_code");
  codigoVinculacion = "";
  Serial.println("Dispositivo vinculado");
  return true;
}

static void prepararCodigoVinculacion() {
  if (dispositivoVinculado || codigoPreparado ||
      WiFi.status() != WL_CONNECTED) {
    return;
  }
  ultimaConsultaVinculacion = millis();

  String url = String(API_BASE_URL) + "/api/v1/dispositivos/" +
               dispositivoId + "/vinculacion/preparar";
  HTTPClient http;
  WiFiClientSecure seguro;
  if (!abrirHttpSeguro(http, seguro, url)) {
    Serial.println("No se pudo iniciar la preparacion del codigo");
    return;
  }

  http.setTimeout(10000);
  http.addHeader("X-Pairing-Code", codigoVinculacion);
  http.addHeader("X-Device-Token", tokenDispositivo);
  int codigoHTTP = http.POST("");
  String payload = codigoHTTP > 0 ? http.getString() : "";
  http.end();
  ultimaConsultaVinculacion = millis();

  if (codigoHTTP == 200) {
    JsonDocument respuesta;
    if (deserializeJson(respuesta, payload)) {
      Serial.println("Respuesta invalida al preparar la vinculacion");
      return;
    }
    String estado = respuesta["estado"] | "";
    if (estado == "completada") {
      marcarDispositivoVinculado();
      return;
    }
    if (estado == "preparada" || estado == "solicitada") {
      codigoPreparado = true;
      mostrarQRVinculacion();
      return;
    }
  }

  if (codigoHTTP == 410) {
    guardarNuevoCodigoVinculacion();
    return;
  }
  if (codigoHTTP == 409 || codigoHTTP == 401) {
    vinculacionRechazada = true;
    pantalla("Vinculacion", "Rechazada", "Revisa el estado", "del dispositivo");
  } else if (codigoHTTP > 0) {
    Serial.printf("Preparacion de vinculacion: HTTP %d\n", codigoHTTP);
  } else {
    Serial.printf("Error HTTP al preparar: %s\n",
                  HTTPClient::errorToString(codigoHTTP).c_str());
  }
}

static void consultarConfirmacionVinculacion() {
  if (dispositivoVinculado || !codigoPreparado || vinculacionRechazada ||
      WiFi.status() != WL_CONNECTED) {
    return;
  }
  ultimaConsultaVinculacion = millis();

  String url = String(API_BASE_URL) + "/api/v1/dispositivos/" +
               dispositivoId + "/vinculacion/confirmar";
  HTTPClient http;
  WiFiClientSecure seguro;
  if (!abrirHttpSeguro(http, seguro, url)) {
    Serial.println("No se pudo iniciar la consulta de vinculacion");
    return;
  }

  http.setTimeout(10000);
  http.addHeader("X-Pairing-Code", codigoVinculacion);
  http.addHeader("X-Device-Token", tokenDispositivo);
  if (aprobacionVinculacionFisica) {
    http.addHeader("X-Pairing-Approval", "confirm");
  }
  int codigoHTTP = http.POST("");
  String payload = codigoHTTP > 0 ? http.getString() : "";
  http.end();
  ultimaConsultaVinculacion = millis();

  if (codigoHTTP == 200) {
    marcarDispositivoVinculado();
  } else if (codigoHTTP == 410) {
    guardarNuevoCodigoVinculacion();
    pantalla("Preparando QR", "Espera...");
  } else if (codigoHTTP == 409 || codigoHTTP == 401) {
    vinculacionRechazada = true;
    pantalla("Vinculacion", "Rechazada",
             "Desvincula el dispositivo", "de la cuenta anterior", "y reinicia");
  } else if (codigoHTTP == 202) {
    JsonDocument respuesta;
    if (deserializeJson(respuesta, payload)) {
      Serial.println("Respuesta invalida al consultar la vinculacion");
      return;
    }
    String estado = respuesta["estado"] | "";
    if (estado == "solicitada") {
      solicitudVinculacionPendiente = true;
      pantalla("Solicitud recibida", "Confirma", "Pulsa BOOT 2 segundos",
               "para vincular");
    } else if (estado == "esperando") {
      solicitudVinculacionPendiente = false;
    }
  } else if (codigoHTTP > 0) {
    Serial.printf("Respuesta de vinculacion: HTTP %d\n", codigoHTTP);
  }
}

static void revisarBotonVinculacion() {
  static uint32_t inicioPresion = 0;
  static bool accionActivada = false;

  if (digitalRead(PIN_RESET_WIFI) != LOW) {
    inicioPresion = 0;
    accionActivada = false;
    return;
  }
  if (inicioPresion == 0) {
    inicioPresion = millis();
    return;
  }

  uint32_t duracionPresion = millis() - inicioPresion;
  if (!accionActivada && !dispositivoVinculado &&
      solicitudVinculacionPendiente &&
      duracionPresion >= VINCULACION_APPROVAL_HOLD_MS) {
    accionActivada = true;
    aprobacionVinculacionFisica = true;
    solicitudVinculacionPendiente = false;
    pantalla("Confirmando", "Vinculacion", "Espera...");
    return;
  }

  if (accionActivada || !dispositivoVinculado ||
      duracionPresion < VINCULACION_BUTTON_HOLD_MS) {
    return;
  }
  accionActivada = true;
  if (!preferencias.putBool("paired", false)) {
    Serial.println("No se pudo guardar el modo de vinculacion");
    pantalla("Error NVS", "Reinicia");
    return;
  }

  dispositivoVinculado = false;
  guardarNuevoCodigoVinculacion();
  acumulador = {};
  inicioPeriodo = millis();
  ultimaMuestra = inicioPeriodo;
  pantalla("Preparando QR", "Espera...");
  prepararCodigoVinculacion();
}

static String abrev(const String &s) {
  if (s == "OPTIMO")
    return "OK";
  if (s == "REPOSO_NOCTURNO")
    return "NOCHE";
  return s; // BAJO / ALTO
}

static void pantalla(const String &linea1, const String &grande,
                     const String &l3, const String &l4, const String &l5) {
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

<<<<<<< HEAD
  String url = String(API_BASE_URL) + "/api/v1/dispositivos/" +
               dispositivoId + "/mediciones";
  HTTPClient http;
  WiFiClientSecure seguro;
  if (!abrirHttpSeguro(http, seguro, url)) {
=======
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
>>>>>>> a1d91d4cc4e18e51e4c15bd2cf241a9d6513bf62
    r.estado = "URL_INVALIDA";
    return r;
  }

  http.setTimeout(15000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", tokenDispositivo);

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

// Detecta si el botón BOOT se mantiene presionado al encender para resetear WiFi.
// El mismo botón, sostenido 5 s con el dispositivo encendido, inicia la vinculación.
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

<<<<<<< HEAD
  cargarCredencialesDispositivo();
=======
  WiFi.setSleep(false);
>>>>>>> a1d91d4cc4e18e51e4c15bd2cf241a9d6513bf62
  pantalla("WiFi OK", WiFi.localIP().toString());
  delay(1500);
  if (!dispositivoVinculado) {
    pantalla("Preparando QR", "Espera...");
    prepararCodigoVinculacion();
  }

  uint32_t ahora = millis();
  inicioPeriodo = ahora;
  ultimaMuestra = ahora - INTERVALO_MUESTREO_MS;
  ultimaConsultaVinculacion = ahora;
}

void loop() {
  uint32_t ahora = millis();
  revisarBotonVinculacion();

  if (!dispositivoVinculado && !vinculacionRechazada &&
      WiFi.status() == WL_CONNECTED &&
      ahora - ultimaConsultaVinculacion >= INTERVALO_VINCULACION_MS) {
    if (codigoPreparado) {
      consultarConfirmacionVinculacion();
    } else {
      prepararCodigoVinculacion();
    }
  }

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

    if (dispositivoVinculado && millis() - inicioPeriodo < INTERVALO_MS) {
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
    if (!dispositivoVinculado) {
      if (WiFi.status() != WL_CONNECTED) {
        WiFi.reconnect();
      }
      acumulador = {};
      inicioPeriodo = millis();
      ultimaMuestra = inicioPeriodo;
      delay(10);
      return;
    }

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
