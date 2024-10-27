#include <ESP8266WiFi.h>     // WiFi library for ESP8266
#include <PubSubClient.h>    // MQTT library
#include <SPI.h>      // Required for SPI communication
#include <LoRa.h>     // LoRa library for Arduino



// Define LoRa module pins
#define SS_PIN 15     // Slave Select pin
#define RST_PIN -1    // Reset pin (not used in this setup)
#define DIO0_PIN 5    // DIO0 pin (used for receive callback)

// Define LoRa frequency (868.1 MHz for Europe)
#define LORA_FREQUENCY 868.1E6  // Frequency in Hz

// Variables for handling user input
String inputMessage = "";   // Stores the message input by the user
bool messageReady = false;  // Flag to indicate when a complete message is ready to send



// WiFi credentials
const char* ssid = "WiFi-EVENT";            // Your WiFi SSID
const char* password = "Sup24@Com25$$";    // Your WiFi Password

// const char* ssid = "macbook";            // Your WiFi SSID
// const char* password = "monther123";    // Your WiFi Password


// MQTT Broker settings
const char* mqtt_server = "4.232.128.55";  // Replace with your cloud MQTT broker address
const int mqtt_port = 1883;                     // Default MQTT port for non-secure connections
const char* mqtt_topic_pub = "gaia-lora-receiver/outgoing";  // Topic to publish messages to
const char* mqtt_topic_sub = "gaia-lora-receiver/incoming";  // Topic to subscribe to for incoming messages


// Custom client ID (must be unique for each device)
const char* clientID = "gateway-Gaia";  // Unique identifier for this MQTT client

WiFiClient espClient;  // Create a WiFi client object
PubSubClient client(espClient);  // Create a PubSubClient object using the WiFi client

// Function to connect to WiFi
void setup_wifi() {
  delay(10);  // Short delay for stability
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);  // Initiate WiFi connection
  while (WiFi.status() != WL_CONNECTED) {  // Wait until WiFi is connected
    delay(500);
    Serial.print(".");  // Print dots while connecting
  }
  Serial.println("WiFi connected");  // Print message when connected
}

// Callback function that runs when an MQTT message arrives
void MQTT_callback(char* topic, byte* payload, unsigned int length) {
  String inputMessage = String((char*)payload).substring(0, length);



  Serial.print("Message arrived [");
  Serial.print(topic);  // Print the topic of the message
  Serial.print("] ");
  Serial.println(inputMessage);


  // Forward MQTT message to LORA endpoint
  LORA_sendMessage(inputMessage);
}

// Function to reconnect to MQTT broker
void reconnect() {
  while (!client.connected()) {  // Loop until we're reconnected
    Serial.print("Attempting MQTT connection...");
    if (client.connect(clientID)) {  // Attempt to connect with the custom client ID
      Serial.println("connected");
      client.subscribe(mqtt_topic_sub);  // Subscribe to the incoming topic
      Serial.println("Subscribed to: " + String(mqtt_topic_sub));
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());  // Print the reason for connection failure
      Serial.println(" trying again in 5 seconds");
      delay(5000);  // Wait 5 seconds before retrying
    }
  }
}



// Function to send a LoRa message
void LORA_sendMessage(String message) {
  Serial.print("Sending message: ");
  Serial.println(message);

  LoRa.beginPacket();  // Start the LoRa packet
  LoRa.print(message);  // Add the message to the packet
  LoRa.endPacket();  // Finish the packet and send it
}

// Function to receive and process a LoRa message
void LORA_receiveMessage() {
  String message = "";  // Variable to store the received message

  // Read the packet
  while (LoRa.available()) {
    message += (char)LoRa.read();  // Read each byte and add it to the message string
  }

  // Print the received message
  Serial.print("Received message: ");
  Serial.println(message);

  // Print the RSSI (Received Signal Strength Indicator)
  Serial.print("RSSI: ");
  Serial.println(LoRa.packetRssi());  // Get and print the RSSI of the received packet


  // Forward LORA message to claud server
  message.trim();  // Remove any leading/trailing whitespace
  
  if (message.length() > 0) {
    // Publish the message to MQTT topic
    client.publish(mqtt_topic_pub, message.c_str());  // Publish message to the outgoing topic
    Serial.println("Published to " + String(mqtt_topic_pub) + ": " + message);  // Confirm publication
  } 
}


// Setup function - runs once when the device starts or resets
void setup() {
  Serial.begin(115200);  // Initialize serial communication at 115200 baud rate
  setup_wifi();  // Call function to connect to WiFi

  // MQTT 
  client.setServer(mqtt_server, mqtt_port);  // Set MQTT server and port
  client.setCallback(MQTT_callback);  // Set the callback function for incoming messages



  // LORA
  while (!Serial);  // Wait for serial port to connect. Needed for native USB port only

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
}

// Main loop function - runs retedly after setup
void loop() {
  if (!client.connected()) {
    reconnect();  // Reconnect to MQTT broker if connection is lost
  }
  client.loop();  // Maintain MQTT connection and process incoming messages

  // Check for any incoming LoRa data
  int packetSize = LoRa.parsePacket();
  if (packetSize) {  // If a packet is received
    LORA_receiveMessage();  // Call function to handle the received message
  }
}