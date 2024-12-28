# Use a base image with Python 3.9 and support for ARM architecture (Raspberry Pi)
FROM balenalib/raspberrypi4-64-python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (ODBC driver, etc.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    unixodbc unixodbc-dev odbcinst odbcinst1debian2 libodbc1 \
    && rm -rf /var/lib/apt/lists/*

# Install Microsoft ODBC Driver 17 for SQL Server (adjust instructions if needed for your specific driver version)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY main.py models.py db_manager.py data_generator.py config.ini pin_mappings.json ./

# Set environment variables for database credentials (fallback to config.ini if not set)
ENV HVAC_DB_USERNAME=${HVAC_DB_USERNAME:-$(awk -F '=' '/username/{print $2}' config.ini)}
ENV HVAC_DB_PASSWORD=${HVAC_DB_PASSWORD:-$(awk -F '=' '/password/{print $2}' config.ini)}

# Command to run the application
CMD ["python", "main.py"]