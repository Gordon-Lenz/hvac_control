import json
import random
import datetime

class DataGenerator:
    def __init__(self, pin_mappings_file):
        with open(pin_mappings_file, 'r') as f:
            self.mappings = json.load(f)
        self.sensor_data = {}
        self.simulated_temperature = 70.0  # Initial temperature in F
        self.simulated_humidity = 45.0  # Initial humidity percentage
        self.simulated_pressure = 14.7  # Initial pressure in PSI
        self.simulated_current = 0.0  # Initial current in Amps
        self.last_update_time = datetime.datetime.now()

    def generate_temperature(self, sensor_name):
        """Generates realistic temperature data."""
        # Simulate temperature fluctuations based on time of day and external factors
        now = datetime.datetime.now()
        time_delta = now - self.last_update_time
        
        # Introduce gradual temperature changes over time
        if "inlet" in sensor_name:
            # Simulate slower temperature changes for inlet
            self.simulated_temperature += random.uniform(-0.05, 0.05) * time_delta.total_seconds() / 60
        else:
            # Simulate faster temperature changes for outlet
            self.simulated_temperature += random.uniform(-0.1, 0.1) * time_delta.total_seconds() / 60

        # Add some random variation
        self.simulated_temperature += random.uniform(-0.2, 0.2)

        # Keep temperature within reasonable bounds
        self.simulated_temperature = max(min(self.simulated_temperature, 90), 50)  # Limit to 50-90 F

        self.last_update_time = now
        return round(self.simulated_temperature, 2)

    def generate_humidity(self):
        """Generates realistic humidity data."""
        # Simulate humidity fluctuations
        self.simulated_humidity += random.uniform(-0.5, 0.5)

        # Keep humidity within reasonable bounds
        self.simulated_humidity = max(min(self.simulated_humidity, 80), 20)  # Limit to 20-80%

        return round(self.simulated_humidity, 2)

    def generate_current(self):
        """Generates realistic current data for a 3-phase system."""
        # Simulate current based on HVAC operation (simplified)
        if 55 < self.simulated_temperature < 75:
            self.simulated_current = random.uniform(0.5, 1.5)  # Low current when idle
        else:
            self.simulated_current = random.uniform(10, 20)  # Higher current when actively heating/cooling

        return round(self.simulated_current, 2)

    def generate_pressure(self):
        """Generates realistic pressure data."""
        # Simulate pressure fluctuations (simplified)
        self.simulated_pressure += random.uniform(-0.1, 0.1)

        # Keep pressure within reasonable bounds
        self.simulated_pressure = max(min(self.simulated_pressure, 15.5), 13.5)  # Limit to 13.5-15.5 PSI

        return round(self.simulated_pressure, 2)

    def get_sensor_readings(self):
        """Returns a dictionary of simulated sensor readings."""
        for sensor_name, sensor_info in self.mappings['sensors'].items():
            if "temperature" in sensor_name:
                self.sensor_data[sensor_name] = self.generate_temperature(sensor_name)
            elif "humidity" in sensor_name:
                self.sensor_data[sensor_name] = self.generate_humidity()
            elif "current" in sensor_name:
                self.sensor_data[sensor_name] = self.generate_current()
            elif "pressure" in sensor_name:
                self.sensor_data[sensor_name] = self.generate_pressure()

        return self.sensor_data 