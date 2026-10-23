
import requests
import pandas as pd


def get_weather_forecast(latitude=12.9716, longitude=77.5946):
    """Fetch hourly weather forecasts for Bengaluru."""

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,cloud_cover",
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        weather = pd.DataFrame({
            "timestamp": data["hourly"]["time"],
            "temperature": data["hourly"]["temperature_2m"],
            "cloud_cover": data["hourly"]["cloud_cover"],
        })

        weather["timestamp"] = pd.to_datetime(weather["timestamp"])
        return weather

    except (requests.RequestException, KeyError, ValueError) as error:
        raise RuntimeError(
            f"Unable to fetch weather forecast: {error}"
        ) from error
