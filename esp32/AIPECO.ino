#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// configuration
const char* ssid = "Infinix NOTE";
const char* password = "aipeco123";

const char* backendUrl = "http://your.backend.url"; // replace with your deployed backend or localhost

// pins
#define DHTPIN 26
#define RELAY1 18
#define RELAY2 19
#define RELAY3 21
#define RELAY4 22

#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// state
unsigned long lastPost = 0;
unsigned long lastPoll = 0;
int currentPollIndex = 0;

void setup() {
  Serial.begin(115200);
  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  pinMode(RELAY3, OUTPUT);
  pinMode(RELAY4, OUTPUT);

  connectWiFi();
  dht.begin();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  unsigned long now = millis();
  
  // Non-blocking JSON POST every 5 seconds
  if (now - lastPost >= 5000) {
    sendSensorData();
    lastPost = now;
  }

  // Non-blocking POLL (poll 1 device every 1.5 seconds to avoid blocking the main loop too long)
  if (now - lastPoll >= 1500) {
    pollNextDeviceCommand();
    lastPoll = now;
  }

  delay(50);
}

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" connected");
}

void sendSensorData() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("Failed to read from DHT sensor!");
    // Defaulting to 0 for fallback instead of returning
    temperature = 0;
    humidity = 0;
  }

  // Payload structure for the deterministic backend calculation
  StaticJsonDocument<200> doc;
  doc["device_id"] = "device1"; // Primary device representing the system (for Temp/Hum)
  doc["current"] = 0;  // Backend does deterministic calculation based on relay states
  doc["voltage"] = 220.0;
  doc["power"] = 0;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;

  String payload;
  serializeJson(doc, payload);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(backendUrl) + "/api/energy/data");
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(payload);
    if (httpResponseCode > 0) {
      String resp = http.getString();
      Serial.println("Posted sensor data: " + resp);
    } else {
      Serial.println("Error posting data: " + String(httpResponseCode));
    }
    http.end();
  }
}

void pollNextDeviceCommand() {
  if (WiFi.status() != WL_CONNECTED) return;
  
  String devices[4] = {"device1", "device2", "device3", "device4"};
  int relayPins[4] = {RELAY1, RELAY2, RELAY3, RELAY4};
  
  String currentDeviceId = devices[currentPollIndex];
  int currentRelayPin = relayPins[currentPollIndex];

  HTTPClient http;
  http.begin(String(backendUrl) + "/api/dashboard/device-command/" + currentDeviceId);
  int code = http.GET();
  
  if (code == HTTP_CODE_OK) {
    String resp = http.getString();
    StaticJsonDocument<200> doc;
    DeserializationError err = deserializeJson(doc, resp);
    if (!err) {
      const char* command = doc["command"]; // "ON" or "OFF"
      if (strcmp(command, "ON") == 0) {
        digitalWrite(currentRelayPin, HIGH);
      } else {
        digitalWrite(currentRelayPin, LOW);
      }
    }
  }
  http.end();

  // Cycle to next device for the next poll
  currentPollIndex = (currentPollIndex + 1) % 4;
}
