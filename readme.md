Okay, here's a user guide that includes environment variables, technical setup information, and references to relevant code blocks in your project files.

# HVAC Control Project - User Guide

## Introduction

This guide provides instructions on setting up and running the HVAC Control Project. This project allows you to monitor and log sensor data from simulated HVAC systems, store it in a SQL Server database, and publish it to an MQTT broker.

## Prerequisites

*   **Hardware:**
    *   Raspberry Pi (Model 3 or 4 recommended) - For a physical setup with sensors and relays.
    *   (Optional) SainSmart 8-Channel Solid State Relay Module, temperature and humidity sensors, current sensors, pressure sensor, jumper wires, power supply for the Raspberry Pi.
*   **Software:**
    *   Windows Operating System (for development and potentially running the MQTT broker)
    *   Python 3.x
    *   SQL Server (with a user that has permissions to create databases and schemas)
    *   Mosquitto MQTT Broker (or another MQTT broker of your choice)
    *   Git (for cloning the repository)

## Installation and Setup

### 1. Clone the Repository

Open a command prompt or PowerShell and clone the project repository from GitHub:

```bash
git clone <repository_url>
cd <repository_name>
```

Replace `<repository_url>` with the actual URL of your project's repository and `<repository_name>` with the name of the directory it creates.

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to isolate project dependencies.

*   **Create:**
    ```bash
    python3 -m venv hvac_env
    ```
*   **Activate:**
    *   **Windows (Command Prompt):**
        ```bash
        hvac_env\Scripts\activate
        ```
    *   **Windows (PowerShell):**
        ```powershell
        .\hvac_env\Scripts\Activate.ps1
        ```

### 3. Install Dependencies

Install the required Python libraries using `pip`:

```bash
pip install -r requirements.txt
```


```1:4:requirements.txt
gpiozero
SQLAlchemy
pyodbc
paho-mqtt
```


### 4. Configure SQL Server

*   **Create a Database:**
    *   Connect to your SQL Server instance using SQL Server Management Studio (SSMS) or another SQL Server client.
    *   Create a new database (e.g., named `hvac`).
*   **Create a User (Recommended):**
    *   Create a new SQL Server login (e.g., `hvac_admin`) with a strong password.
    *   Grant this user the necessary permissions on the `hvac` database:
        *   `db_datareader`
        *   `db_datawriter`
        *   `db_ddladmin` (to create schemas and tables)

### 5. Configure `config.ini`

*   **Database Settings:**
    *   Open the `config.ini` file in a text editor.
    *   Under the `[DATABASE]` section, update the following:
        *   `server`: The hostname or IP address of your SQL Server instance (e.g., `localhost\SQLEXPRESS` for a local SQL Server Express instance).
        *   `database`: The name of the database you created (e.g., `hvac`).
        *   `username`: The SQL Server username (e.g., `hvac_admin`).
        *   `password`: The password for the SQL Server user.
        *   `driver`: The ODBC driver to use (e.g., `ODBC Driver 17 for SQL Server`).
        *   `trusted_connection`: Set to `yes` if you are using Windows Authentication; otherwise, set to `no`.


```5:11:config.ini
[DATABASE]
server = localhost\SQLEXPRESS
database = hvac
username = hvac_admin
password = p
driver = ODBC Driver 17 for SQL Server
trusted_connection = False
```


*   **HVAC Unit ID:**
    *   Under the `[HVAC]` section, set the `hvac_unit_id` to a unique identifier for your HVAC unit (e.g., `uno`). This will be used to create a separate schema in the database for each unit.


```13:14:config.ini
[HVAC]
hvac_unit_id = uno
```


*   **MQTT Broker Address:**
    *   Under the `[MQTT]` section, set the `broker_address` to the hostname or IP address of your MQTT broker (e.g., `localhost` if running Mosquitto locally).


```20:21:config.ini
[MQTT]
broker_address = localhost
```


### 6. (Optional) Configure Mosquitto MQTT Broker (Windows)

If you don't have an MQTT broker set up, you can install and configure Mosquitto:

*   **Install:** Download and install Mosquitto from [https://mosquitto.org/download/](https://mosquitto.org/download/).
*   **Secure:**
    1. **Create a Password File:**
        *   Open a Command Prompt as administrator.
        *   Navigate to `C:\Program Files\mosquitto`.
        *   Run: `mosquitto_passwd -c mosquitto.passwd <username>` (replace `<username>` with your desired username, e.g., `hvac`). Enter a password when prompted.
    2. **Configure Mosquitto:**
        *   Edit `C:\Program Files\mosquitto\mosquitto.conf`.
        *   Add the following lines:
            ```
            allow_anonymous false
            password_file C:\Program Files\mosquitto\mosquitto.passwd
            ```
    3. **Restart Mosquitto:**
        *   Open Services (search in the Start menu).
        *   Find "Mosquitto Broker" and restart it.

### 7. (Optional) Configure Pin Mappings (`pin_mappings.json`)

If you are using physical sensors and relays, update the `pin_mappings.json` file to match your wiring:


```1:49:pin_mappings.json
{
  "relays": {
    "HVAC_POWER": {
      "relay_num": 1,
      "pin": 17
    },
    "HEATING_MODE": {
      "relay_num": 2,
      "pin": 18
    },
    "COOLING_MODE": {
      "relay_num": 3,
      "pin": 27
    }
  },

    "sensors": {
      "temperature_inlet": {
        "pin": 4, 
        "description": "Ambient temperature sensor inlet"
      },
      "temperature_outlet": {
        "pin": 5, 
        "description": "Ambient temperature sensor outlet"
      },
      "humidity": {
        "pin": 17,
        "description": "Humidity sensor in the main hallway"
      },
      "current_phase1": {
        "pin": 22,
        "description": "Current sensor for phase 1 of the HVAC power supply"
      },
      "current_phase2": {
        "pin": 23,
        "description": "Current sensor for phase 2 of the HVAC power supply"
      },
      "current_phase3": {
        "pin": 24,
        "description": "Current sensor for phase 3 of the HVAC power supply"
      },
      "pressure": {
        "pin": 25,
        "description": "Pressure sensor in the HVAC duct"
      }
    }
  
} 
 
```


*   **`relays`:** Defines the relay numbers and GPIO pins connected to each HVAC function (e.g., power, heating mode, cooling mode).
*   **`sensors`:** Defines the GPIO pins and descriptions for each sensor (e.g., temperature inlet, temperature outlet, humidity, current, pressure).

### 8. Set Environment Variables

To securely manage sensitive information like database and MQTT credentials, it's recommended to use environment variables.

**Windows (Permanent):**

1. Search for "environment variables" in the Start menu and select "Edit the system environment variables."
2. Click "Environment Variables...".
3. Under "System variables" (or "User variables"), click "New...".
4. Set the following variables:

    *   **`HVAC_DB_USERNAME`:** Your SQL Server username (fallback: `config.ini` `[DATABASE]` `username`).
    *   **`HVAC_DB_PASSWORD`:** Your SQL Server password (fallback: `config.ini` `[DATABASE]` `password`).
    *   **`MQTT_BROKER_ADDRESS`:** Your MQTT broker address (fallback: `config.ini` `[MQTT]` `broker_address`).
    *   **`MQTT_USERNAME`:** Your MQTT username (fallback: `config.ini` `[MQTT]` `username`).
    *   **`MQTT_PASSWORD`:** Your MQTT password (fallback: `config.ini` `[MQTT]` `password`).
5. Click "OK" on all open windows.
6. Restart your command prompt or PowerShell for changes to take effect.

### 9. Run the Application

1. Make sure your SQL Server and MQTT broker are running.
2. Activate your virtual environment (if not already active).
3. Run the `main.py` script:

```bash
python main.py
```

## Code Structure

*   **`main.py`:** The main entry point of the application. It initializes the database, MQTT client, data generator, and handles the main control loop.


*   **`mqtt_manager.py`:** Handles MQTT communication, including connecting, subscribing to topics, publishing messages, and handling dynamic configuration updates.
*   **`db_manager.py`:** Handles database interactions, including initializing the database, creating schemas and tables, and inserting sensor data.
*   **`data_generator.py`:** Generates simulated sensor data for testing purposes.
*   **`models.py`:** Defines the SQLAlchemy database models.
*   **`config.ini`:** Stores configuration settings for the database, MQTT, and other parameters.
*   **`pin_mappings.json`:** (Optional) Stores the mappings between GPIO pins and relays/sensors.
*   **`requirements.txt`:** Lists the required Python libraries.

## Dynamic Configuration

You can dynamically update the `averaging_interval` setting by publishing a message to the `hvac/config` MQTT topic with the following JSON payload:

```json
{
    "GLOBAL": {
        "averaging_interval": <new_value>
    }
}
```

Replace `<new_value>` with the desired averaging interval in seconds. The `main.py` script will automatically reload the configuration and apply the new setting.

## Troubleshooting

*   **Database Connection Errors:**
    *   Verify that your SQL Server instance is running.
    *   Check your database credentials in `config.ini` or environment variables.
    *   Ensure that the specified user has the necessary permissions on the database.
*   **MQTT Connection Errors:**
    *   Verify that your MQTT broker is running.
    *   Check your MQTT broker address, username, and password in `config.ini` or environment variables.
    *   If using Mosquitto with authentication, make sure you have created a password file and configured `mosquitto.conf` correctly.
*   **Logging:**
    *   The application logs informational messages to the console and errors to `hvac_control.log`. Check these logs for any error messages or debugging information.

## Further Development

*   **Implement Physical Sensor and Relay Control:** Replace the simulated data generator with code to read from actual sensors and control relays using the `gpiozero` library.
*   **Add HVAC Control Logic:** Implement control algorithms in `main.py` to manage HVAC functions based on sensor readings and configuration settings.
*   **Web Interface/Mobile App:** Develop a front-end interface for remote monitoring and control of the HVAC system.
*   **Scheduling and Automation:** Add features to schedule HVAC operations and create automation rules.

