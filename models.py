import datetime

from sqlalchemy import Column, Integer, String, Float, Index, text
from sqlalchemy.dialects.mssql import DATETIMEOFFSET
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

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
        'timestamp': Column(DATETIMEOFFSET, server_default=func.sysdatetimeoffset(), index=True)  # Use server-generated DateTimeOffset
    }
    for sensor_name, sensor_info in sensor_mappings.items():
        attributes[sensor_name] = Column(Float, nullable=True)  # Create a column for each sensor

    HvacSensorData = type('HvacSensorData', (Base,), attributes)  # Dynamically create the class

    return HvacSensorData