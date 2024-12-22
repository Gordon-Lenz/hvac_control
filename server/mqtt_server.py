# server/mqtt_server.py
import paho.mqtt.client as mqtt
import json
import pandas as pd
import configparser
from shared.decorators import log_exceptions  # Import the decorator
from weather_api import get_weather_data

# Create a dictionary to store DataFrames for each unit
unit_dfs = {}

def on_connect(client, userdata, flags, rc):
    """
    Callback function for when the client connects to the MQTT broker.
    """
    # ... (same as before)

@log_exceptions  # Apply the decorator
def on_message(client, userdata, msg):
    """
    Callback function for when a message is received on a subscribed topic.
    """
    # ... (same as before)

# ... (rest of the mqtt_server.py code)