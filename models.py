import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def create_models(schema_name, sensor_mappings):
    """
    Dynamically creates SQLAlchemy models with table names based on the schema name
    and columns based on the provided sensor mappings.
    """

    # Dynamically define the columns for HvacSensorData
    attributes = {
        '__tablename__': 'sensor_data',
        '__table_args__': {'schema': schema_name},
        'id': Column(Integer, primary_key=True),
        'timestamp': Column(DateTime, index=True, default=datetime.datetime.now(datetime.timezone.utc))
    }
    for sensor_name, sensor_info in sensor_mappings.items():
        attributes[sensor_name] = Column(Float, nullable=True)  # Create a column for each sensor

    HvacSensorData = type('HvacSensorData', (Base,), attributes)  # Dynamically create the class

    return HvacSensorData