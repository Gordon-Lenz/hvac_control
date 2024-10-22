# HVAC Control Project

This project aims to automate and control multiple HVAC (Heating, Ventilation, and Air Conditioning) systems using a Raspberry Pi, solid-state relays (SSRs), and a SQL Server database for storing sensor data and configuration settings.

## Features (Planned)

* **Sensor Data Logging:** Collect and store temperature, humidity, current, and pressure data from sensors connected to the Raspberry Pi.
* **HVAC Control:** Control various HVAC functions (e.g., power, mode, fan speed) based on sensor readings, configuration settings, and potentially user input.
* **Database Integration:**  Use a SQL Server database with separate schemas for each HVAC unit to store sensor data and configuration options.
* **Dynamic Configuration:**  Synchronize configuration settings between a `config.ini` file and the database.
* **Remote Control (Future):**  Potentially implement a web interface or mobile app for remote monitoring and control of the HVAC system.
* **Scheduling and Automation (Future):**  Add the ability to schedule HVAC operations and create automation rules based on various conditions.

## Hardware Requirements

* Raspberry Pi (Model 3 or 4 recommended)
* SainSmart 8-Channel Solid State Relay Module
* Temperature and Humidity Sensors (specific models to be determined)
* Current Sensors (for 3-phase power monitoring)
* Pressure Sensor
* Jumper wires
* Power supply for the Raspberry Pi

## Software Requirements

* Python 3
* Libraries:
    * gpiozero
    * SQLAlchemy
    * pyodbc

## Installation and Setup

1. Clone this repository to your Raspberry Pi.
2. Create a virtual environment: `python3 -m venv hvac_env`
3. Activate the virtual environment: `source hvac_env/bin/activate`
4. Install the required libraries: `pip install -r requirements.txt`
5. Configure your SQL Server connection details in `config.ini`.
6. Update `pin_mappings.json` with your actual sensor and relay pin assignments.
7. Run the `main.py` script.

## Usage

* The script will create the necessary database schema and tables if they don't exist.
* It will start logging sensor data to the database.
* You'll need to implement your HVAC control logic in the `main.py` file based on your specific requirements.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve this project.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.