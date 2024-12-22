import random
import time

def simulate_sensor_data(sensor_mappings):
    """
    Generates simulated sensor data based on the provided mappings.
    """
    sensor_data = {}
    for sensor_name, sensor_info in sensor_mappings.items():
        if sensor_name == "temperature":
            # Simulate temperature between 68 and 78 degrees Fahrenheit
            sensor_data[sensor_name] = round(random.uniform(68, 78), 2)
        elif sensor_name == "humidity":
            # Simulate humidity between 30% and 60%
            sensor_data[sensor_name] = round(random.uniform(30, 60), 2)
        elif sensor_name.startswith("current_phase"):
            # Simulate current between 5 and 15 amps
            sensor_data[sensor_name] = round(random.uniform(5, 15), 2)
        elif sensor_name == "pressure":
            # Simulate pressure between 1000 and 1020 Pa
            sensor_data[sensor_name] = round(random.uniform(1000, 1020), 2)
        else:
            # Default simulation for other sensor types
            sensor_data[sensor_name] = round(random.uniform(0, 100), 2)

    return sensor_data