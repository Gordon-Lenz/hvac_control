# server/weather_api.py
import asyncio
from python_weather import Client

async def get_weather_data(location="Maryville, TN"):
    """
    Retrieves current weather data using the python-weather library.
    """
    async with Client(format=Client.IMPERIAL) as client:  # Use imperial units
        try:
            weather = await client.find(location)

            # Extract relevant data (customize as needed)
            relevant_data = {
                "temperature": weather.current.temperature,
                "humidity": weather.current.humidity,
                "description": weather.current.description
            }
            return relevant_data

        except Exception as e:
            print(f"Error: Could not retrieve weather data - {e}")
            return None