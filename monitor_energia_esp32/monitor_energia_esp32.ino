#include <WiFiManager.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "EmonLib.h"
#include <Preferences.h>
#include <ArduinoOTA.h>           // Biblioteca OTA
#include <WebServer.h>
#include <ZMPT101B.h>

#define BUFFER_SIZE 500
#define PIN_CORRENTE 34
#define PIN_TENSAO 35
#define SENSITIVITY 952.0f


WebServer httpServer(80);
const char* firmwareVersion = "v1.0.0";
unsigned long startMillis;

struct EnergiaPacket {
  float corrente;
  float tensao;
  float potencia;
};

EnergiaPacket buffer[BUFFER_SIZE];
int bufferStart = 0;
int bufferEnd = 0;
bool bufferCheio = false;

WebSocketsClient webSocket;
EnergyMonitor emonCorrente;
ZMPT101B sensorTensao(PIN_TENSAO, 60.0); // pino e frequencia da rede
Preferences prefs;

// Parâmetros customizáveis
String serverIP;
String serverPort;
String authToken;
String deviceID;
unsigned long intervalo = 500;

const float calib_corrente = 6.0606f;

unsigned long lastSend = 0;

// ----------------------------
//     CONFIGURAÇÃO OTA
// ----------------------------
const char* otaHostname = "esp32-monitor";
const char* otaPassword = "att_esp32";  // escolha uma senha forte

// ----------------------------
//        FUNÇÕES OTA
// ----------------------------
void setupOTA() {
  ArduinoOTA.setHostname(otaHostname);
  ArduinoOTA.setPassword(otaPassword);

  ArduinoOTA.onStart([]() {
    Serial.println("OTA: Iniciando atualização...");
  });
  ArduinoOTA.onEnd([]() {
    Serial.println("\nOTA: Atualização concluída!");
  });
  ArduinoOTA.onProgress([](unsigned int progress, unsigned int total) {
    Serial.printf("OTA: Progresso %u%%\r", (progress / (total / 100)));
  });
  ArduinoOTA.onError([](ota_error_t err) {
    Serial.printf("OTA: Erro[%u]: ", err);
    if (err == OTA_AUTH_ERROR)    Serial.println("Auth falhou");
    else if (err == OTA_BEGIN_ERROR) Serial.println("Início falhou");
    else if (err == OTA_CONNECT_ERROR) Serial.println("Conexão falhou");
    else if (err == OTA_RECEIVE_ERROR) Serial.println("Recebimento falhou");
    else if (err == OTA_END_ERROR)   Serial.println("Finalização falhou");
  });

  ArduinoOTA.begin();
  Serial.println("OTA configurada e aguardando atualizações...");
}

// ----------------------------
//     EVENT HANDLER WS
// ----------------------------
void webSocketEvent(WStype_t type, uint8_t* payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.println("[WS] Conectado! Enviando buffer offline...");
      // assim que conectar, descarrega o buffer
      while (bufferStart != bufferEnd || (bufferCheio && bufferStart == bufferEnd)) {
        EnergiaPacket p = buffer[bufferStart];
        StaticJsonDocument<256> doc;
        doc["corrente"]  = p.corrente;
        doc["tensao"]    = p.tensao;
        doc["potencia"]  = p.potencia;
        doc["token"]     = authToken;
        doc["device_id"] = deviceID;
        String jsonOut;
        serializeJson(doc, jsonOut);
        webSocket.sendTXT(jsonOut);
        bufferStart = (bufferStart + 1) % BUFFER_SIZE;
        bufferCheio = false;
        delay(10);
      }
      break;

    case WStype_DISCONNECTED:
      Serial.println("[WS] Desconectado!");
      break;

    default:
      break;
  }
}

// ----------------------------
//      SETUP PRINCIPAL
// ----------------------------
void setup() {
  Serial.begin(115200);

  startMillis = millis();
  // Ler da flash
  prefs.begin("settings", true);
  serverIP    = prefs.getString("server", "192.168.1.107");
  serverPort  = prefs.getString("port", "5000");
  authToken   = prefs.getString("token", "9fGx2pL7qVb5Zr1C");
  deviceID    = prefs.getString("device", "ESP001");
  intervalo   = prefs.getUInt("interval", 500);
  prefs.end();

  // Portal Captive para WiFi + parâmetros
  WiFiManager wifiManager;
  WiFiManagerParameter param_server("server", "Servidor IP", serverIP.c_str(), 40);
  WiFiManagerParameter param_port("port", "Porta", serverPort.c_str(), 6);
  WiFiManagerParameter param_token("token", "Auth Token", authToken.c_str(), 32);
  WiFiManagerParameter param_device("device", "Device ID", deviceID.c_str(), 20);
  WiFiManagerParameter param_interval("interval", "Intervalo (ms)", String(intervalo).c_str(), 6);
  wifiManager.addParameter(&param_server);
  wifiManager.addParameter(&param_port);
  wifiManager.addParameter(&param_token);
  wifiManager.addParameter(&param_device);
  wifiManager.addParameter(&param_interval);

  if (!wifiManager.autoConnect("ESP-Setup")) {
    Serial.println("Falha ao conectar WiFi. Reiniciando...");
    ESP.restart();
  }

  // Salvar na flash
  prefs.begin("settings", false);
  prefs.putString("server", param_server.getValue());
  prefs.putString("port", param_port.getValue());
  prefs.putString("token", param_token.getValue());
  prefs.putString("device", param_device.getValue());
  prefs.putUInt("interval", String(param_interval.getValue()).toInt());
  prefs.end();


  Serial.println("Configuração carregada:");
  Serial.println(" Server: "   + serverIP + ":" + serverPort);
  Serial.println(" Token: "    + authToken);
  Serial.println(" Device: "   + deviceID);
  Serial.println(" Intervalo: "+ String(intervalo) + " ms");

  httpServer.on("/restart", HTTP_POST, []() {
    httpServer.send(200, "application/json", "{\"status\":\"Reiniciando...\"}");
    delay(100);       // deixa a resposta ir embora
    ESP.restart();    // reinicia o chip
  });

  httpServer.on("/health", HTTP_GET, []() {
    StaticJsonDocument<256> doc;

    // RAM / Heap
    doc["free_heap"]      = ESP.getFreeHeap();        // bytes livres
    doc["min_free_heap"]  = ESP.getMinFreeHeap();     // mínimo já alcançado
    doc["psram_free"]     = ESP.getPsramSize() ? ESP.getFreePsram() : 0;

    // CPU
    doc["cpu_freq_mhz"]   = ESP.getCpuFreqMHz();      // frequência atual

    // Flash usage via SPIFFS
    // FSInfo info;
    // SPIFFS.info(info);
    // doc["flash_total"]    = info.totalBytes;          // bytes totais
    // doc["flash_used"]     = info.usedBytes;           // bytes usados
    // doc["flash_free"]     = info.totalBytes - info.usedBytes;

    String out;
    serializeJson(doc, out);
    httpServer.send(200, "application/json", out);
  });

  httpServer.on("/status", HTTP_GET, []() {
    StaticJsonDocument<256> doc;
    doc["device_id"] = deviceID;
    doc["firmware_version"] = firmwareVersion;
    doc["uptime_s"] = (millis() - startMillis) / 1000;
    doc["rssi"] = WiFi.RSSI();
    String out;
    serializeJson(doc, out);
    httpServer.send(200, "application/json", out);
  });

  httpServer.on("/config", HTTP_GET, []() {
    StaticJsonDocument<256> doc;
    doc["serverIP"]    = serverIP;
    doc["serverPort"]  = serverPort;
    doc["intervalo"]   = intervalo;
    doc["authToken"]   = authToken;
    doc["deviceID"]    = deviceID;
    String out;
    serializeJson(doc, out);
    httpServer.send(200, "application/json", out);
  });

   // POST /config — recebe JSON e atualiza as configurações
  httpServer.on("/config", HTTP_POST, []() {
    String body = httpServer.arg("plain");
    Serial.println(">>> POST /config body: " + body);

    StaticJsonDocument<256> doc;
    auto err = deserializeJson(doc, body);
    if (err) {
      Serial.println("JSON inválido: " + String(err.c_str()));
      httpServer.send(400, "application/json", "{\"error\":\"JSON inválido\"}");
      return;
    }

    bool salvou = false;
    prefs.begin("settings", false);

    // Debug: imprimir o que estava antes
    Serial.println("Antes de gravar:");
    Serial.println("  serverIP   = " + prefs.getString("server", "(none)"));
    Serial.println("  serverPort = " + prefs.getString("port", "(none)"));
    Serial.println("  intervalo  = " + String(prefs.getUInt("interval", 0)));

    if (doc.containsKey("serverIP")) {
      serverIP = doc["serverIP"].as<String>();
      prefs.putString("server", serverIP);
      salvou = true;
      Serial.println("Atualizando serverIP para " + serverIP);
    }
    if (doc.containsKey("serverPort")) {
      serverPort = doc["serverPort"].as<String>();
      prefs.putString("port", serverPort);
      salvou = true;
      Serial.println("Atualizando serverPort para " + serverPort);
    }
    if (doc.containsKey("intervalo")) {
      intervalo = doc["intervalo"].as<unsigned long>();
      prefs.putUInt("interval", intervalo);
      salvou = true;
      Serial.println("Atualizando intervalo para " + String(intervalo));
    }
    // … outros campos …

    prefs.end();

    // Debug: ler de volta
    prefs.begin("settings", true);
    Serial.println("Depois de gravar:");
    Serial.println("  serverIP   = " + prefs.getString("server", "(none)"));
    Serial.println("  serverPort = " + prefs.getString("port", "(none)"));
    Serial.println("  intervalo  = " + String(prefs.getUInt("interval", 0)));
    prefs.end();

    if (!salvou) {
      httpServer.send(400, "application/json", "{\"error\":\"Nenhum campo válido fornecido\"}");
      return;
    }

    httpServer.send(200, "application/json", "{\"status\":\"Configuração atualizada\"}");
  });


  // SPIFFS.begin(true);
  httpServer.begin();
  
  analogReadResolution(12);
  analogSetPinAttenuation(PIN_TENSAO, ADC_11db);
  analogSetPinAttenuation(PIN_CORRENTE, ADC_11db);

  // Inicializa sensores
  emonCorrente.current(PIN_CORRENTE, calib_corrente);
  sensorTensao.setSensitivity(SENSITIVITY);

  // Inicializa WebSocket
  webSocket.begin(serverIP.c_str(), serverPort.toInt(), "ws");
  webSocket.onEvent(webSocketEvent);
  webSocket.setReconnectInterval(5000);

  // Inicializa OTA
  setupOTA();
}

// ----------------------------
//      LOOP PRINCIPAL
// ----------------------------
void loop() {
  webSocket.loop();
  ArduinoOTA.handle();   // mantém o OTA ativo
  httpServer.handleClient();

  unsigned long now = millis();
  if (now - lastSend > intervalo) {
    lastSend = now;

    // Leitura de sensores
    emonCorrente.calcIrms(1480);

    // Empilha no buffer
    EnergiaPacket novo{emonCorrente.Irms, sensorTensao.getRmsVoltage(10), emonCorrente.Irms * sensorTensao.getRmsVoltage(10)};
    buffer[bufferEnd] = novo;
    bufferEnd = (bufferEnd + 1) % BUFFER_SIZE;
    if (bufferEnd == bufferStart) {
      bufferCheio = true;
      bufferStart = (bufferStart + 1) % BUFFER_SIZE;
    }

    // Se conectado, descarrega buffer
    if (webSocket.isConnected()) {
      webSocketEvent(WStype_CONNECTED, nullptr, 0);
    }
  }
}
