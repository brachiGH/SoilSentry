import paho.mqtt.client as mqtt
import mysql.connector
from datetime import datetime, timedelta
import time
from meteo import weather

# Configuration for connecting to MySQL
config = {
    'user': 'GaiaDatabaseUser',  # Replace with your MySQL username
    'password': 'brahimAZE123',  # Replace with your MySQL password
    'host': 'localhost',  # Replace with your MySQL host, if not localhost
    'database': 'GaiaBase'
}



# Define the callback function for when a message is published
def on_publish(client, userdata, mid):
    print("Message published with mid: {}".format(mid))

# Define the callback for when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully!")
    else:
        print("Connection failed with code", rc)

def sendduration(duration):
    # Create an MQTT client instance
    client = mqtt.Client()

    # Assign the callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish

    # Connect to the MQTT broker (update the host and port as necessary)
    client.connect("localhost", 1883, 60)

    # Publish the message
    topic = "gaia-lora-receiver/incoming"
    result = client.publish(topic, duration)

    # Check if the publish was successful
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("Message sent successfully.")
    else:
        print("Failed to send message.")

    # Loop to process network traffic and callbacks
    client.loop_start()

    # Optional: wait for a moment before disconnecting
    import time
    time.sleep(2)

    # Disconnect from the broker
    client.loop_stop()
    client.disconnect()


def get_last_lat_and_lng():
    # Connect to the MySQL database
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()
    # Query to fetch the most recent lat and lng
    query = """
    SELECT lat, lng 
    FROM sensor_data2 
    ORDER BY timestamp DESC 
    LIMIT 1
    """
    cursor.execute(query)

    # Fetch the result
    result = cursor.fetchone()

    # Display the result
    if result:
        lat, lng = result
        print(f"Last Latitude: {lat}, Last Longitude: {lng}")
    else:
        print("No data found.")

    # Close the cursor and connection
    cursor.close()
    connection.close()

    return result;


# Function to determine irrigation needs
def check_irrigation():
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()

        # Calculate the timestamp for 24 hours ago
        one_day_ago = datetime.now() - timedelta(days=1)

        # Query to fetch data from the past 24 hours
        query = """
        SELECT soil_moisture, temperature, humidity, timestamp 
        FROM sensor_data 
        WHERE timestamp >= %s
        """
        cursor.execute(query, (one_day_ago,))

        results = cursor.fetchall()

        # Define thresholds and base irrigation time
        moisture_threshold = 30  # Moisture percentage threshold
        base_irrigation_time = 600  # Base irrigation time in seconds (10 minutes)
        irrigation_time = 0
        
        for row in results:
            soil_moisture, temperature, humidity, timestamp = row
            
            # Check if soil moisture is below the threshold
            if soil_moisture < moisture_threshold:
                # Calculate irrigation time adjustments based on temperature and humidity
                temp_factor = 1 + (temperature - 25) * 0.05  # Adjust based on temperature
                humidity_factor = 1 - (humidity / 100)  # Adjust based on humidity
                irrigation_time += base_irrigation_time * temp_factor * humidity_factor

        # If irrigation is needed, return the time in seconds
        if irrigation_time > 0:
            print(f"Irrigation needed for {irrigation_time:.2f} seconds.")

            lat, lng = get_last_lat_and_lng()
            irrigation_decision = weather(lat, lng)
            if (irrigation_decision):
                sendduration(irrigation_time*1000)
        else:
            print("No irrigation needed.")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        # Close the connection
        if connection.is_connected():
            cursor.close()
            connection.close()

while(True):
    check_irrigation()
    # 3 hour delay
    time.sleep(1000*60*60*3)
