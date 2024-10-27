import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

def should_irrigate(hourly_dataframe):
    # Define thresholds
    high_precipitation_probability = 50  # percent
    significant_rain = 5  # mm
    high_temperature = 30  # Celsius (soil or air temperature)
    
    # Look at the next few hours of weather data (e.g., next 6 hours)
    next_hours = hourly_dataframe.head(6)

    # Check for rain and precipitation probability
    avg_precipitation_probability = next_hours["precipitation_probability"].mean()
    total_rain = next_hours["rain"].sum()

    # Check for high temperatures that might require irrigation
    avg_soil_temperature_0cm = next_hours["soil_temperature_0cm"].mean()

    # Decision based on weather conditions
    if total_rain > significant_rain:
        print("No irrigation needed: Significant rain forecasted.")
        return False
    elif avg_precipitation_probability > high_precipitation_probability:
        print("No irrigation needed: High chance of precipitation.")
        return False
    elif avg_soil_temperature_0cm > high_temperature:
        print("Irrigation needed: High soil temperature detected.")
        return True
    else:
        print("Irrigation needed: Low rain and precipitation probability.")
        return True

def weather(lat, lng):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": [
            "temperature_2m", 
            "relative_humidity_2m", 
            "precipitation_probability", 
            "rain", 
            "soil_temperature_0cm", 
            "soil_temperature_6cm", 
            "soil_temperature_18cm"
        ],
        "past_days": 7
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()} {response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process hourly data
    hourly = response.Hourly()
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ),
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
        "precipitation_probability": hourly.Variables(2).ValuesAsNumpy(),
        "rain": hourly.Variables(3).ValuesAsNumpy(),
        "soil_temperature_0cm": hourly.Variables(4).ValuesAsNumpy(),
        "soil_temperature_6cm": hourly.Variables(5).ValuesAsNumpy(),
        "soil_temperature_18cm": hourly.Variables(6).ValuesAsNumpy(),
    }

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    print(hourly_dataframe)

    # Determine if irrigation is needed based on weather data
    irrigation_needed = should_irrigate(hourly_dataframe)
    return irrigation_needed

# # Example usage with coordinates
# lat, lng = 52.5200, 13.4050  # Berlin, Germany
# irrigation_decision = weather(lat, lng)
# print(f"Irrigation decision: {'Yes' if irrigation_decision else 'No'}")
