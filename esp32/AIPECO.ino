#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// configuration
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

const char* backendUrl = "http://your.backend.url"; // replace with your deployed backend or localhost

// pins
#define DHTPIN 32
#define RELAY1 26
#define RELAY2 27
#define RELAY3 25
#define RELAY4 33

#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

// state
float simulatedCurrent = 0;
unsigned long lastPost = 0;
unsigned long lastPoll = 0;

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
  if (now - lastPost > 5000) {
    sendSensorData();
    lastPost = now;
  }

  if (now - lastPoll > 5000) {
    pollCommands();
    lastPoll = now;
  }

  controlRelaysByTemp();
  delay(200);
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
    return;
  }

  // simulate current between 0.5 and 5A
  simulatedCurrent = 0.5 + random(0, 4500) / 1000.0;
  float voltage = 220.0;
  float power = simulatedCurrent * voltage;

  StaticJsonDocument<200> doc;
  doc["device_id"] = "device1"; // update with actual ID stored or configured
  doc["current"] = simulatedCurrent;  // backend expects 'current' field
  doc["voltage"] = voltage;
  doc["power"] = power;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;

  String payload;
  serializeJson(doc, payload);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    // FastAPI route: POST /api/energy/data
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

void pollCommands() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(String(backendUrl) + "/api/dashboard/device-command/device1");
    int code = http.GET();
    if (code == HTTP_CODE_OK) {
      String resp = http.getString();
      Serial.println("Command response: " + resp);
      // parse JSON to set relays if necessary
      StaticJsonDocument<200> doc;
      DeserializationError err = deserializeJson(doc, resp);
      if (!err) {
        const char* status = doc["status"];
        if (strcmp(status, "on") == 0) {
          digitalWrite(RELAY1, HIGH);
        } else {
          digitalWrite(RELAY1, LOW);
        }
        // for multiple relays, extend payload with pin/command
      }
    }
    http.end();
  }
}

void controlRelaysByTemp() {
  float temperature = dht.readTemperature();
  if (isnan(temperature)) return;
  // simple threshold logic
  if (temperature > 30) {
    digitalWrite(RELAY1, LOW);
    digitalWrite(RELAY2, LOW);
    digitalWrite(RELAY3, LOW);
    digitalWrite(RELAY4, LOW);
  }
}
