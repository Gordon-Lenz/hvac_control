# mqtt_client.py
import json
from asyncio_mqtt import Client, MqttError

async def on_connect(client):
    """
    Callback function for when the client connects to the MQTT broker.
    """
    print("Connected to MQTT Broker!")
    # Subscribe to relevant topics (e.g., for receiving commands or setpoints)
    await client.subscribe("hvac/commands")

async def on_message(message):
    """
    Callback function for when a message is received on a subscribed topic.
    """
    print(f"Received message: {message.payload.decode()} on topic: {message.topic}")
    # ... (Add logic to process the received message and take action)

async def publish_sensor_data(client, sensor_data, hvac_unit_id):
    """
    Publishes sensor data to an MQTT topic, including the hvac_unit_id.
    """
    try:
        topic = f"hvac/{hvac_unit_id}/sensor_data"  # Include hvac_unit_id in the topic
        await client.publish(topic, json.dumps(sensor_data.get_mqtt_data()))
    except MqttError as error:
        print(f'Error publishing to MQTT: {error}')

async def create_mqtt_client(mqtt_config):
    """
    Creates and configures the MQTT client.
    """
    try:
        async with Client(mqtt_config['broker'], int(mqtt_config['port'])) as client:
            await on_connect(client)  # Call the on_connect callback
            # ... (rest of your MQTT logic - you'll likely call publish_sensor_data from here)
    except MqttError as error:
        print(f'Error connecting to MQTT broker: {error}')