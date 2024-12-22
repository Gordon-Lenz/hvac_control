# server/mqtt_server.py
import sys
sys.path.append('..')  # Add the parent directory to the Python path
import asyncio
import json
import pandas as pd
import configparser
from aiomqtt import Client as mqtt
from ..shared.decorators import log_exceptions  # Import the decorator
from weather_api import get_weather_data  # Import the get_weather_data function


# Create a dictionary to store DataFrames for each unit
unit_dfs = {}

def on_connect(client, userdata, flags, rc):
    """
    Callback function for when the client connects to the MQTT broker.
    """
    if rc == 0:
        print("MQTT Server connected to broker!")
        # Subscribe to all topics under "hvac/"
        client.subscribe("hvac/#")  
    else:
        print("Failed to connect, return code %d\n", rc)

@log_exceptions  # Apply the decorator
def on_message(client, userdata, msg):
    """
    Callback function for when a message is received on a subscribed topic.
    """
    global unit_dfs  # Access the global dictionary of DataFrames

    try:
        # Parse the JSON payload
        sensor_data = json.loads(msg.payload.decode())

        # Extract the unit ID from the topic
        unit_id = msg.topic.split("/")[1]  

        # Get the DataFrame for the current unit, create it if it doesn't exist
        if unit_id not in unit_dfs:
            unit_dfs[unit_id] = pd.DataFrame(columns=sensor_data.keys())  # Use keys from sensor_data as columns

        # Append the sensor data to the DataFrame for the current unit
        unit_dfs[unit_id] = unit_dfs[unit_id].append(sensor_data, ignore_index=True)

        # Print the updated DataFrame for the current unit
        print(f"Updated sensor data DataFrame for unit {unit_id}:")
        print(unit_dfs[unit_id])

        # ... (Add your logic here to further process the DataFrame)

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON payload: {e}")

async def create_mqtt_server(mqtt_config):
    """
    Creates and configures the MQTT server (client).
    """
    server = mqtt.Client()
    server.on_connect = on_connect
    server.on_message = on_message

    # Set up authentication (if required)
    if 'username' in mqtt_config and 'password' in mqtt_config:
        server.username_pw_set(mqtt_config['username'], mqtt_config['password'])

    # Connect to the MQTT broker
    server.connect(mqtt_config['broker'], int(mqtt_config['port']))
    return server

async def main():
    """
    Main function to run the MQTT server and publish weather data.
    """
    # --- Configuration ---
    config = configparser.ConfigParser()
    config.read('../config.ini')  # Assuming you have the MQTT config in config.ini
    mqtt_config = config['MQTT']

    # Create and start the MQTT server
    mqtt_server = await create_mqtt_server(mqtt_config)  # Use the helper function

    # Get weather data and publish it
    weather_data = await get_weather_data()  # Use the asynchronous get_weather_data function
    if weather_data:
        mqtt_server.publish("hvac/weather", json.dumps(weather_data))  # Publish to a "weather" topic

    # Keep the server running
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())