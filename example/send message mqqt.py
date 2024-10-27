import paho.mqtt.client as mqtt

# Define the callback function for when a message is published
def on_publish(client, userdata, mid):
    print("Message published with mid: {}".format(mid))

# Define the callback for when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully!")
    else:
        print("Connection failed with code", rc)

def sendduration():
    # Create an MQTT client instance
    client = mqtt.Client()

    # Assign the callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish

    # Connect to the MQTT broker (update the host and port as necessary)
    client.connect("localhost", 1883, 60)

    # Publish the message
    topic = "gaia-lora-receiver/incoming"
    duration = "10000" # 10  second
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
    time.sleep(1)

    # Disconnect from the broker
    client.loop_stop()
    client.disconnect()


sendduration()