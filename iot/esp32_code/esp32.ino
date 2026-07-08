/**
 * Smart Irrigation System Using IoT and Machine Learning
 * Final Year Engineering Project - ESP32 Firmware
 * 
 * Hardware Connections:
 * 1. Soil Moisture Sensor: Analog Pin A0 (GPIO 34)
 * 2. DHT11 Temp/Humidity: Digital Pin GPIO 4 (Pull-up resistor 10k suggested)
 * 3. Rain Sensor: Analog Pin A1 (GPIO 35)
 * 4. Relay Module (Pump Control): Digital Pin GPIO 2
 * 5. Status LED: GPIO 15 (Optional status indicator)
 * 
 * Required Arduino IDE Libraries:
 * - DHT sensor library by Adafruit
 * - Adafruit Unified Sensor
 * - ArduinoJson (v6.x or newer)
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ==========================================
// CONFIGURATION PARAMETERS
// ==========================================
// Replace with your local WiFi Router credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Replace with your Flask Backend Server IP address (Run 'ipconfig' on Windows cmd)
// Note: If running on local computer, Flask binds to PC's local IP (e.g., 192.168.1.15)
const char* serverUrl = "http://192.168.1.15:5000/api/sensor-data";

// ==========================================
// PIN ALLOCATIONS
// ==========================================
#define SOIL_MOISTURE_PIN 34  // GPIO 34 (ADC1_CH6)
#define RAIN_SENSOR_PIN   35  // GPIO 35 (ADC1_CH7)
#define DHTPIN            4   // GPIO 4
#define DHTTYPE           DHT11
#define RELAY_PIN         2   // GPIO 2 (Controls Pump Relay)
#define STATUS_LED_PIN    15  // GPIO 15 (Blinks when posting)

DHT dht(DHTPIN, DHTTYPE);

// Loop delay (Sends data every 5 seconds as requested)
const unsigned long sendInterval = 5000;
unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n==========================================");
  Serial.println("Smart Irrigation System - ESP32 Firmware");
  Serial.println("==========================================");
  
  // Pin modes
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  
  // Initial state: Pump OFF (Assuming Active-High relay. For Active-Low, set HIGH)
  digitalWrite(RELAY_PIN, LOW); 
  digitalWrite(STATUS_LED_PIN, LOW);
  
  // Init sensors
  dht.begin();
  Serial.println("Sensors initialized.");
  
  // Connect to WiFi
  connectWiFi();
}

void loop() {
  // Check Wifi status and reconnect if lost
  if (WiFi.status() != WL_CONNECTED) {
    reconnectWiFi();
  }
  
  unsigned long currentMillis = millis();
  
  // Send data at defined interval
  if (currentMillis - lastSendTime >= sendInterval) {
    lastSendTime = currentMillis;
    
    // Read sensors
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();
    int rawMoisture = analogRead(SOIL_MOISTURE_PIN);
    int rawRain = analogRead(RAIN_SENSOR_PIN);
    
    // Check if readings failed and write dummy values if needed
    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("[ERROR] Failed to read from DHT sensor! Using simulation fallback.");
      temperature = 27.5; // dummy fallback
      humidity = 60.0;
    }
    
    // Convert analog moisture (0-4095 on ESP32 12-bit ADC) to percentage (0-100%)
    // Note: Soil moisture sensor output is usually inversely proportional:
    // Dry soil = high analog output (~4095), Wet soil = low analog output (~1000)
    float moisturePercent = mapAnalogToPercent(rawMoisture, 4095, 1000);
    
    // Convert rain analog reading (0-4095) to percentage/level
    // Dry sensor = ~4095, Wet sensor = ~0-1500
    float rainPercent = mapAnalogToPercent(rawRain, 4095, 0); 
    
    Serial.println("\n--- Sensor Telemetry Reads ---");
    Serial.print("Soil Moisture: "); Serial.print(moisturePercent); Serial.println("%");
    Serial.print("Temperature: "); Serial.print(temperature); Serial.println(" °C");
    Serial.print("Humidity: "); Serial.print(humidity); Serial.println("%");
    Serial.print("Rain Value: "); Serial.println(rainPercent);
    
    // Send data to API
    postSensorData(moisturePercent, temperature, humidity, rainPercent);
  }
}

// Helper to convert ESP32 ADC values to percent
float mapAnalogToPercent(int value, int dryVal, int wetVal) {
  float percent = (float)(value - dryVal) / (float)(wetVal - dryVal) * 100.0;
  if (percent < 0.0) percent = 0.0;
  if (percent > 100.0) percent = 100.0;
  return percent;
}

void connectWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi Connected successfully!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WARNING] WiFi Connection failed! Will retry in loop.");
  }
}

void reconnectWiFi() {
  Serial.println("[WIFI] Connection lost! Reconnecting...");
  WiFi.disconnect();
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 10) {
    delay(1000);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Reconnected successfully!");
  }
}

void postSensorData(float moisture, float temp, float hum, float rain) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] Post aborted. WiFi not connected.");
    return;
  }
  
  digitalWrite(STATUS_LED_PIN, HIGH); // Turn LED on during call
  
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON Payload
  StaticJsonDocument<200> doc;
  doc["moisture"] = moisture;
  doc["temperature"] = temp;
  doc["humidity"] = hum;
  doc["rain_value"] = rain;
  
  String jsonPayload;
  serializeJson(doc, jsonPayload);
  
  Serial.print("[HTTP] Posting payload: ");
  Serial.println(jsonPayload);
  
  int httpResponseCode = http.POST(jsonPayload);
  
  if (httpResponseCode > 0) {
    Serial.print("[HTTP] Response code: ");
    Serial.println(httpResponseCode);
    
    if (httpResponseCode == HTTP_CODE_CREATED || httpResponseCode == HTTP_CODE_OK) {
      String responseBody = http.getString();
      Serial.print("[HTTP] Server Response: ");
      Serial.println(responseBody);
      
      // Parse Response JSON
      StaticJsonDocument<200> responseDoc;
      DeserializationError error = deserializeJson(responseDoc, responseBody);
      
      if (!error) {
        const char* pumpStatus = responseDoc["pump_status"]; // "ON" or "OFF"
        const char* systemMode = responseDoc["mode"];        // "AUTO" or "MANUAL"
        
        Serial.print("[SYS] Sync -> Mode: ");
        Serial.print(systemMode);
        Serial.print(" | Pump Status: ");
        Serial.println(pumpStatus);
        
        // Control pump relay
        if (strcmp(pumpStatus, "ON") == 0) {
          digitalWrite(RELAY_PIN, HIGH); // Turn pump ON
          Serial.println("[ACTUATOR] Pump set to ON");
        } else {
          digitalWrite(RELAY_PIN, LOW);  // Turn pump OFF
          Serial.println("[ACTUATOR] Pump set to OFF");
        }
      } else {
        Serial.print("[JSON] Deserialization failed: ");
        Serial.println(error.f_str());
      }
    }
  } else {
    Serial.print("[HTTP] POST failed. Error: ");
    Serial.println(http.errorToString(httpResponseCode).c_str());
  }
  
  http.end();
  digitalWrite(STATUS_LED_PIN, LOW); // Turn off LED
}
