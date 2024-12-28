import configparser
import json
import logging
import paho.mqtt.client as mqtt
import time

class MQTTManager:
    def __init__(self, config_file, broker_address, topic):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        self.broker_address = broker_address
        self.topic = topic
        self.client = mqtt.Client()
        self.client.on_message = self.on_message
        self.config_reload_callback = None

    def on_message(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            logging.info(f"Received message on topic '{message.topic}': {payload}")

            if message.topic == self.topic:
                self.handle_config_update(payload)
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")

    def handle_config_update(self, payload):
        if 'GLOBAL' in payload:
            global_config = payload['GLOBAL']
            if 'averaging_interval' in global_config:
                new_averaging_interval = global_config['averaging_interval']
                # Update the averaging interval in the config file
                self.config.set('GLOBAL', 'averaging_interval', str(new_averaging_interval))
                with open('config.ini', 'w') as configfile:
                    self.config.write(configfile)
                logging.info(f"Updated averaging_interval to {new_averaging_interval} in config.ini")

                # Call the callback function to reload the configuration
                if self.config_reload_callback:
                    self.config_reload_callback()

    def set_config_reload_callback(self, callback):
        self.config_reload_callback = callback

    def connect(self, username=None, password=None):
        try:
            if username and password:
                self.client.username_pw_set(username, password)
            self.client.connect(self.broker_address, 1883, 60)
            self.client.loop_start()
            self.client.subscribe(self.topic)
            logging.info(f"Connected to MQTT broker at {self.broker_address} and subscribed to topic '{self.topic}'")
        except Exception as e:
            logging.error(f"Failed to connect to MQTT broker: {e}")

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        logging.info("Disconnected from MQTT broker")

    def publish(self, topic, message):
        try:
            # Serialize the message to JSON if it's a dictionary
            if isinstance(message, dict):
                message = json.dumps(message)
            self.client.publish(topic, message)
            logging.info(f"Published message to topic '{topic}': {message}")
        except TypeError as e:
            logging.error(f"Failed to publish message: {e}")
        except Exception as e:
            logging.error(f"Failed to publish message: {e}")

# Example usage (not to be run directly)
if __name__ == '__main__':
    mqtt_manager = MQTTManager('config.ini', 'localhost', 'hvac/config')
    mqtt_manager.connect()

    # To publish a message for testing:
    # mqtt_manager.publish(json.dumps({"GLOBAL": {"polling_interval": 5}}))

    try:
        while True:
            pass  # Keep the script running to receive messages
    except KeyboardInterrupt:
        mqtt_manager.disconnect() 