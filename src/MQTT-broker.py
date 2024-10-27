import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import errorcode
import json


# Configuration for connecting to MySQL
config = {
    'user': 'GaiaDatabaseUser',
    'password': 'brahimAZE123',
    'host': 'localhost',
    'database': 'GaiaBase'
}



# Define the callback function for when a message is received
def on_message(client, userdata, message):
    try:
        insert_json_data(str(message.payload.decode("utf-8")))
    except mysql.connector.Error as err:
        print(f"Failed loading data in server (invalid json): {err}")
        exit(1)
    print(f"Topic: {message.topic}\nMessage: {message.payload.decode()}")

# Define the callback function for when the client connects to the broker
def on_connect(client, userdata, flags, rc):

    # Connect to MySQL server
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Create database and table if not exists
    create_database_if_not_exists(cursor)
    create_table_if_not_exists(cursor)

    print(f"Connected with result code {rc}")
    client.subscribe("gaia-lora-receiver/outgoing")


    cursor.close()
    conn.close()


def create_database_if_not_exists(cursor):
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS GaiaBase")
        print("Database 'GaiaBase' checked/created.")
    except mysql.connector.Error as err:
        print(f"Failed creating database: {err}")
        exit(1)

def create_table_if_not_exists(cursor):
    cursor.execute("USE GaiaBase")
    table_creation_query = """
    CREATE TABLE IF NOT EXISTS sensor_data2 (
        id INT AUTO_INCREMENT PRIMARY KEY,
        soil_moisture INT NOT NULL,
        temperature FLOAT NOT NULL,
        humidity FLOAT NOT NULL,
        lat FLOAT NOT NULL,
        lng FLOAT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    try:
        cursor.execute(table_creation_query)
        print("Table 'sensor_data' checked/created.")
    except mysql.connector.Error as err:
        print(f"Failed creating table: {err}")
        exit(1)

def insert_json_data(json_data):
    try:
        # Connect to MySQL server
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()


        # Parse JSON data
        data = json.loads(json_data)
        soil_moisture = data.get('soil_moisture')
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        lat = data.get('lat')
        lng = data.get('lng')

        # Insert data into table
        insert_query = """
        INSERT INTO sensor_data2 (soil_moisture, temperature, humidity, lat, lng)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (soil_moisture, temperature, humidity, lat, lng))
        conn.commit()
        print("Data inserted successfully.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        conn.close()



# Create an MQTT client instance
client = mqtt.Client()

# Set the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker running on the same server
client.connect("localhost", 1883, 60)

# Start the loop to process network traffic and dispatch callbacks
client.loop_forever()
