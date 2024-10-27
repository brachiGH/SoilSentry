// Include necessary libraries
#include <SPI.h>      // Required for SPI communication
#include <LoRa.h>     // LoRa library for Arduino
#include <DHT.h>
#include <ArduinoJson.h>
#include <TinyGPSPlus.h>
#include <SoftwareSerial.h>

#define max_soilMoisture 600
#define min_soilMoisture  0


// Create software serial for GPS module
static const int RXPin = 20, TXPin = 21;
static const uint32_t GPSBaud = 9600;

// The TinyGPSPlus object
TinyGPSPlus gps;

// The serial connection to the GPS device
SoftwareSerial gpsSerial(RXPin, TXPin);


// Define LoRa module pins
#define SS_PIN 10     // Slave Select pin
#define RST_PIN 9     // Reset pin 
#define DIO0_PIN 7    // DIO0 pin (used for receive callback)

// Define LoRa frequency (868.1 MHz for Europe)
#define LORA_FREQUENCY 868.1E6  // Frequency in Hz

// DHT22 Settings
#define DHTPIN 2          // Pin connected to the DHT22 data pin
#define DHTTYPE DHT22     // DHT22 sensor type
DHT dht(DHTPIN, DHTTYPE);

#define SOIL_MOISTURE_PIN A0
#define RELAY_PIN 8

// Variables for handling user input
String inputMessage = "";   // Stores the message input by the user
bool messageReady = false;  // Flag to indicate when a complete message is ready to send


// Timing variables
unsigned long previousMillis = 0;  // Stores last time sensor data was read
// const long interval = 120000;      // Interval at which to read sensors (2 minutes)
const long interval = 10000;      // Interval at which to read sensors (10 second)



float randomValue[] = {21.6, 18.9, 46.7, 59.7, 62.6, 68.8, 67.3, 71.7, 67.7, 68.9, 67.4, 68.6,67.4, 67.4, 69.6};
int i = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  while (!Serial);  // Wait for serial port to connect. Needed for native USB port only
  
  // Initialize DHT22 sensor
  dht.begin();

  pinMode(DHTPIN, INPUT);  // Explicitly set the data pin as OUTPUT for DHT22 (though it's handled by dht.begin())
  pinMode(SOIL_MOISTURE_PIN, INPUT); // Set soil moisture sensor pin as INPUT
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  gpsSerial.begin(GPSBaud);

  Serial.println("LoRa Bidirectional Communication (868.1 MHz)");

  // Configure LoRa transceiver module
  LoRa.setPins(SS_PIN, RST_PIN, DIO0_PIN);

  // Initialize LoRa
  if (!LoRa.begin(LORA_FREQUENCY)) {
    Serial.println("LoRa initialization failed. Check your connections.");
    while (1);  // If failed, do nothing
  }

  // Set LoRa parameters
  LoRa.setSpreadingFactor(12);  // Set spreading factor (6-12). Higher SF increases range but decreases data rate
  LoRa.setSyncWord(0xF3);       // Set sync word to ensure communication only between nodes with the same sync word

  Serial.println("LoRa initialization successful.");
  Serial.println("Type a message and press enter to send via LoRa.");

    randomSeed(analogRead(1));  // Seed the random number generator
}

void loop() {
  // Check for any incoming LoRa data
  int packetSize = LoRa.parsePacket();
  if (packetSize) {  // If a packet is received
    receiveMessage();  // Call function to handle the received message
  }


  unsigned long currentMillis = millis();
  
  // Check if it's time to read the sensors
  if (currentMillis - previousMillis >= interval) {
    // Save the last time the sensors were read
    previousMillis = currentMillis;

    // Create a JSON object
    StaticJsonDocument<200> doc;

    // Read soil moisture sensor value
    int soilMoistureValue = analogRead(SOIL_MOISTURE_PIN);

    // sensor calibration
    float soilMoisture_reading = (soilMoistureValue/(2^10 - 1 )) * 3.3; // V_reading = (ADC_Reading/(2^ADC_bits - 1 )) * V_supply
    float soilMoisture_Percentage = (soilMoisture_reading - min_soilMoisture)*100 / (max_soilMoisture - min_soilMoisture);
    // map any soilMoisture in the range [min_soilMoisture°C, max_soilMoisture°C] to a percentage between 0% and 100%.

    doc["soil_moisture"] = randomValue[i];
    i++;


    // Read DHT22 sensor data
    float temperature = dht.readTemperature();  // Get temperature in Celsius
    float humidity = dht.readHumidity();        // Get humidity in percentage

    // Check if any reads failed
    if (isnan(temperature) || isnan(humidity)) {
      doc["error"] = "Failed to read from DHT sensor!";
      doc["temperature"] = 0;
      doc["humidity"] = 0;
    } else {
      // Add temperature and humidity to JSON object
      doc["temperature"] = temperature;
      doc["humidity"] = humidity;
    }
    float* pos = getGPS();
    doc["lng"] = pos[0];
    doc["lat"] = pos[1];

    // Serialize JSON object to string and print it
    String output;
    serializeJson(doc, output);
    sendMessage(output);
    delete[] pos;
  }
}

// Function to send a LoRa message
void sendMessage(String message) {
  Serial.print("Sending message: ");
  Serial.println(message);

  LoRa.beginPacket();  // Start the LoRa packet
  LoRa.print(message);  // Add the message to the packet
  LoRa.endPacket();  // Finish the packet and send it
}

// Function to receive and process a LoRa message
void receiveMessage() {
  String message = "";  // Variable to store the received message

  // Read the packet
  while (LoRa.available()) {
    message += (char)LoRa.read();  // Read each byte and add it to the message string
  }

  if (message == "hello from the claud") {
    sendMessage("hello back! from endpoint device");
    return;
  }

  // Print the received message
  Serial.print("Received message: ");
  Serial.println(message);

  // Print the RSSI (Received Signal Strength Indicator)
  Serial.print("RSSI: ");
  Serial.println(LoRa.packetRssi());  // Get and print the RSSI of the received packet

  digitalWrite(RELAY_PIN, 1);
  delay(strtol(message.c_str(), nullptr, 10));
  digitalWrite(RELAY_PIN, 0);
}


float* getGPS() {
  float* pos = new float[2]{10.1906103, 36.8920991}; // Dynamically allocate memory for two floats

  while (gpsSerial.available()) {
    gps.encode(gpsSerial.read());
    
    if (gps.location.isUpdated()) {
      pos[0] = gps.location.lng();
      pos[1] = gps.location.lat(); 
    }
  }

  return pos; // Remember to delete this memory later to avoid memory leaks
}