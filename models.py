# models.py
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
        '__tablename__': f'{schema_name}_sensor_data',
        '__table_args__': {'schema': schema_name},
        'id': Column(Integer, primary_key=True),
        'timestamp': Column(DateTime, index=True, default=datetime.datetime.now(datetime.timezone.utc))
    }
    for sensor_name, sensor_info in sensor_mappings.items():
        attributes[sensor_name] = Column(Float, nullable=True) 
        attributes[f'{sensor_name}_description'] = Column(String(100), default=sensor_info.get('description'))

    HvacSensorData = type('HvacSensorData', (Base,), attributes)

    class HvacConfig(Base):  
        __tablename__ = f'{schema_name}_config'  
        __table_args__ = {'schema': schema_name}
        id = Column(Integer, primary_key=True)
        section = Column(String(50))  
        option = Column(String(50))   
        value = Column(String(100))
        timestamp = Column(DateTime, index=True, default=datetime.datetime.now(datetime.timezone.utc)) 

    return HvacSensorData, HvacConfig