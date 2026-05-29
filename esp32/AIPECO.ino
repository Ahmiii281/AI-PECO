#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <math.h>
#include <ArduinoJson.h>

// =============================================================
//  AI-PECOo — ESP32 Firmware v2.0
//  AI-Powered Energy Consumption Optimizer
//
//  WIRING (unchanged from your hardware setup):
//    SCT-013 Current Sensor  → GPIO 34 (analog)
//    DHT22 Data              → GPIO 4
//    Relay IN1               → GPIO 14
//    Relay IN2               → GPIO 27
//    Relay IN3               → GPIO 26
//    Relay IN4               → GPIO 25
//    All relays are ACTIVE LOW (LOW = ON, HIGH = OFF)
// =============================================================

// ===== PIN DEFINITIONS (DO NOT CHANGE — matches physical wiring) =====
#define SCT_PIN   34
#define IN1       14
#define IN2       27
#define IN3       26
#define IN4       25
#define DHTPIN     4

// ===== DHT SETUP =====
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// ===== INCLUDE CREDENTIALS FROM credentials.h =====
// IMPORTANT: Create credentials.h from credentials.h.example
// and configure your WiFi SSID, password, and backend URL
#include "credentials.h"

// If credentials.h not found, use defaults (will not connect)
#ifndef WIFI_SSID
  #define WIFI_SSID "UNCONFIGURED_SSID"
  #define WIFI_PASSWORD "UNCONFIGURED_PASSWORD"
  #define BACKEND_URL "http://127.0.0.1:8000"
  #define DEVICE_API_KEY "unconfigured_key"
#endif

// Convert C strings to Arduino Strings
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;
String serverBase = BACKEND_URL;
String deviceApiKey = DEVICE_API_KEY;

// ===== DEVICE IDs =====
// These are the MongoDB ObjectId strings for your 4 devices.
// After starting the backend, check console logs or the dashboard
// to get the actual device IDs, then paste them here.
//
// The backend's demo seeder auto-creates 4 devices. To find their IDs:
//   1. Start the backend: python main.py
//   2. Login at the dashboard as admin@aipeco.com / admin123
//   3. Go to Devices page — each device shows its ID
//   4. Or call: GET http://<your-ip>:8000/api/devices (with JWT token)
//
// For now, these map to:
//   device1 → Relay IN1 (GPIO 14) — e.g. "Living Room AC"
//   device2 → Relay IN2 (GPIO 27) — e.g. "Kitchen Appliances"
//   device3 → Relay IN3 (GPIO 26) — e.g. "Water Heater"
//   device4 → Relay IN4 (GPIO 25) — e.g. "Bedroom Fan"
//
// IMPORTANT: Replace these placeholder strings with actual MongoDB ObjectIds!
String deviceIds[] = {
  "device1",   // → IN1 (GPIO 14)
  "device2",   // → IN2 (GPIO 27)
  "device3",   // → IN3 (GPIO 26)
  "device4",   // → IN4 (GPIO 25)
};

// Map device index → relay GPIO pin
const int RELAY_PINS[] = { IN1, IN2, IN3, IN4 };
const int NUM_DEVICES  = 4;

// ===== CONSTANTS =====
const float VREF          = 3.3;
const int   ADC_RES       = 4095;
const float CURRENT_RATIO = 60.0;
const float VOLTAGE       = 220.0;

// ===== CURRENT SPIKE DETECTION =====
float lastCurrent    = 0;
float spikeThreshold = 0.5;   // Amps — adjust based on testing

// ===== TIMING =====
unsigned long lastSensorSend    = 0;
unsigned long lastCommandPoll   = 0;
unsigned long lastWiFiReconnectAttempt = 0;
const unsigned long SENSOR_INTERVAL  = 5000;   // Send sensor data every 5 s
const unsigned long COMMAND_INTERVAL = 1500;   // Poll relay commands every 1.5 s
const unsigned long WIFI_RECONNECT_INTERVAL = 10000; // Reconnect interval 10 s

// Which device index to poll next (cycles 0→1→2→3→0→...)
int pollIndex = 0;

// =====================================================================
//  FUNCTION: Read RMS current from SCT-013
// =====================================================================
float getCurrent() {
  float sum = 0;

  for (int i = 0; i < 400; i++) {
    int adc = analogRead(SCT_PIN);
    float voltage = (adc / (float)ADC_RES) * VREF;
    float centered = voltage - (VREF / 2.0);
    sum += centered * centered;
  }

  float rms = sqrt(sum / 400.0);
  return rms * CURRENT_RATIO;
}

// =====================================================================
//  FUNCTION: Connect to WiFi
// =====================================================================
void connectWiFi() {
  Serial.print("[WIFI] Connecting");
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println(" Connected!");
    Serial.print("[WIFI] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println(" FAILED — will retry in loop.");
  }
}

// =====================================================================
//  FUNCTION: POST sensor data to /api/energy/data
//
//  The backend expects:
//    { device_id, current, voltage, power, temperature, humidity }
//
//  NOTE: The backend currently overrides current/voltage/power with
//  its own deterministic calculation based on relay state. But we
//  still send the real sensor values for logging and future use.
// =====================================================================
void sendSensorData(String deviceId, float temp, float hum, float current, float power) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = serverBase + "/api/energy/data";

  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", deviceApiKey);

  // Build JSON payload matching EnergyDataCreate schema
  StaticJsonDocument<256> doc;
  doc["device_id"]    = deviceId;
  doc["current"]      = current;
  doc["voltage"]      = VOLTAGE;
  doc["power"]        = power;
  doc["temperature"]  = temp;
  doc["humidity"]     = hum;

  String payload;
  serializeJson(doc, payload);

  int httpCode = http.POST(payload);

  if (httpCode == 200 || httpCode == 201) {
    Serial.printf("[DATA] %s → %d OK\n", deviceId.c_str(), httpCode);
  } else if (httpCode > 0) {
    Serial.printf("[DATA] %s → %d\n", deviceId.c_str(), httpCode);
  } else {
    Serial.printf("[DATA] %s → ERROR: %s\n",
                  deviceId.c_str(), http.errorToString(httpCode).c_str());
  }

  http.end();
}

// =====================================================================
//  FUNCTION: Poll relay command for ONE device
//  GET /api/dashboard/device-command/{device_id}
//
//  Returns: { device_id, command: "ON"/"OFF", relay_pin }
//  No authentication required on this endpoint.
//
//  We cycle through devices one at a time to spread the load.
// =====================================================================
void pollDeviceCommand(int deviceIndex) {
  if (WiFi.status() != WL_CONNECTED) return;
  if (deviceIndex < 0 || deviceIndex >= NUM_DEVICES) return;

  HTTPClient http;
  String url = serverBase + "/api/dashboard/device-command/" + deviceIds[deviceIndex];

  http.begin(url);
  int httpCode = http.GET();

  if (httpCode == 200) {
    String response = http.getString();

    StaticJsonDocument<256> doc;
    DeserializationError err = deserializeJson(doc, response);

    if (!err) {
      const char* command = doc["command"];
      int relayPin = RELAY_PINS[deviceIndex];

      // ACTIVE LOW logic:
      //   "ON"  → relay energized → pin LOW
      //   "OFF" → relay off       → pin HIGH
      if (strcmp(command, "ON") == 0) {
        digitalWrite(relayPin, LOW);
      } else {
        digitalWrite(relayPin, HIGH);
      }

      Serial.printf("[RELAY] Device %d (pin %d) → %s\n",
                    deviceIndex + 1, relayPin, command);
    }
  } else if (httpCode == 404) {
    // Device not found in backend — ignore silently
    // This happens when device IDs haven't been configured yet
  } else if (httpCode > 0) {
    Serial.printf("[RELAY] Device %d → HTTP %d\n", deviceIndex + 1, httpCode);
  } else {
    Serial.printf("[RELAY] Device %d → ERROR: %s\n",
                  deviceIndex + 1, http.errorToString(httpCode).c_str());
  }

  http.end();
}

// =====================================================================
//  SETUP
// =====================================================================
void setup() {
  Serial.begin(115200);
  delay(100);

  Serial.println("\n========================================");
  Serial.println("  AI-PECOo  —  ESP32 Firmware v2.0");
  Serial.println("  Energy Consumption Optimizer");
  Serial.println("========================================");
  Serial.println();

  // Initialize DHT sensor
  dht.begin();

  // Initialize relay pins as OUTPUT
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // ACTIVE LOW — all relays OFF at startup
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, HIGH);

  // ADC configuration for SCT-013 current sensor
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);

  // Connect to WiFi
  connectWiFi();

  Serial.println("[SETUP] Pin mapping:");
  Serial.println("  IN1 (GPIO 14) → Device 1");
  Serial.println("  IN2 (GPIO 27) → Device 2");
  Serial.println("  IN3 (GPIO 26) → Device 3");
  Serial.println("  IN4 (GPIO 25) → Device 4");
  Serial.println();
  Serial.printf("[SETUP] Server: %s\n", serverBase.c_str());
  Serial.println("[SETUP] Ready — entering main loop...\n");
}

// =====================================================================
//  LOOP
// =====================================================================
void loop() {
  unsigned long now = millis();

  // ── Reconnect WiFi if dropped ──
  if (WiFi.status() != WL_CONNECTED) {
    unsigned long now_wifi = millis();
    if (now_wifi - lastWiFiReconnectAttempt >= WIFI_RECONNECT_INTERVAL) {
      Serial.println("[WIFI] Connection lost. Attempting reconnect...");
      WiFi.disconnect();
      WiFi.begin(ssid, password);
      lastWiFiReconnectAttempt = now_wifi;
    }
  }

  // ══════════════════════════════════════════════════════════════
  //  SENSOR DATA — Read & send every SENSOR_INTERVAL (5 seconds)
  // ══════════════════════════════════════════════════════════════
  if (now - lastSensorSend >= SENSOR_INTERVAL) {
    lastSensorSend = now;

    // Read DHT22
    float temp = dht.readTemperature();
    float hum  = dht.readHumidity();

    if (isnan(temp) || isnan(hum)) {
      Serial.println("[DHT] Read error — skipping this cycle.");
    } else {
      // Read SCT-013 current sensor
      float current = getCurrent();
      float power   = current * VOLTAGE;

      // Serial output
      Serial.println("────────────────────────────────────");
      Serial.printf("  Temp:    %.1f °C\n", temp);
      Serial.printf("  Hum:     %.1f %%\n", hum);
      Serial.printf("  Current: %.2f A\n", current);
      Serial.printf("  Power:   %.1f W\n", power);
      Serial.println("────────────────────────────────────");

      // Send data for EACH device (all share the same physical sensors)
      // The backend stores data per-device for analytics and anomaly detection.
      for (int i = 0; i < NUM_DEVICES; i++) {
        sendSensorData(deviceIds[i], temp, hum, current, power);
      }

      // Track current for spike detection (local awareness)
      float delta = current - lastCurrent;
      if (delta > spikeThreshold) {
        Serial.printf("[ALERT] ⚡ Current spike: +%.2fA (%.2fA → %.2fA)\n",
                      delta, lastCurrent, current);
      }
      lastCurrent = current;
    }
  }

  // ══════════════════════════════════════════════════════════════
  //  RELAY COMMANDS — Poll one device per cycle (every 1.5 sec)
  //  Cycles through device1 → device2 → device3 → device4 → ...
  //
  //  When a user toggles a relay on the web dashboard:
  //    Dashboard → POST /api/dashboard/relay/{id} → sets is_relay_on
  //    ESP32 polls GET /api/dashboard/device-command/{id} → gets ON/OFF
  //    ESP32 sets GPIO pin accordingly
  // ══════════════════════════════════════════════════════════════
  if (now - lastCommandPoll >= COMMAND_INTERVAL) {
    lastCommandPoll = now;

    pollDeviceCommand(pollIndex);

    // Advance to next device
    pollIndex = (pollIndex + 1) % NUM_DEVICES;
  }

  // Small yield to prevent watchdog reset
  delay(10);
}
