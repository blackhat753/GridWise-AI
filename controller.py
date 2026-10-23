
import numpy as np
import pandas as pd

from data_generator import generate_training_data
from models import train_models, predict_load, predict_solar
from energy_manager import calculate_energy_balance
from weather_service import get_weather_forecast


def run_forecast(
    transformer_limit=150,
    battery_capacity=40,
    weather_cond="Sunny Day",
    missing_data_pct=15,
):
    """Run the complete forecasting and mitigation pipeline."""

    if transformer_limit <= 0:
        raise ValueError("Transformer limit must be positive.")

    if battery_capacity < 0:
        raise ValueError("Battery capacity cannot be negative.")

    if not 0 <= missing_data_pct <= 100:
        raise ValueError("Missing data percentage must be between 0 and 100.")

    # Generate training data and train forecasting models
    training_data = generate_training_data()
    load_model, solar_model, features = train_models(training_data)

    # Prepare the next 24 hours
    forecast_dates = pd.date_range(
        start=pd.Timestamp.now().floor("h"),
        periods=24,
        freq="h",
    )

    forecast = pd.DataFrame({"timestamp": forecast_dates})
    forecast["hour"] = forecast["timestamp"].dt.hour
    forecast["dayofweek"] = forecast["timestamp"].dt.day_of_week
    forecast["is_weekend"] = (
        forecast["dayofweek"].isin([5, 6]).astype(int)
    )

    forecast["sin_hour"] = np.sin(
        2 * np.pi * forecast["hour"] / 24
    )
    forecast["cos_hour"] = np.cos(
        2 * np.pi * forecast["hour"] / 24
    )

    # Apply real weather data or a simulated scenario
    if weather_cond == "Real Weather Forecast (Bengaluru)":
        weather_data = get_weather_forecast()

        weather_data["timestamp"] = pd.to_datetime(
            weather_data["timestamp"]
        )
        forecast = forecast.merge(
            weather_data,
            on="timestamp",
            how="left",
        )

        # Fill missing weather readings safely
        forecast["temperature"] = (
            forecast["temperature"].interpolate().ffill().bfill()
        )
        forecast["cloud_cover"] = (
            forecast["cloud_cover"].interpolate().ffill().bfill()
        )

    elif weather_cond == "Sunny Day":
        forecast["cloud_cover"] = 10.0
        forecast["temperature"] = (
            24.0
            + 6 * np.sin(
                (forecast["hour"] - 8) * np.pi / 12
            )
        )

    elif weather_cond == "Cloudy Afternoon (Solar Drop)":
        forecast["cloud_cover"] = np.where(
            forecast["hour"].between(13, 18),
            85.0,
            15.0,
        )
        forecast["temperature"] = (
            22.0
            + 4 * np.sin(
                (forecast["hour"] - 8) * np.pi / 12
            )
        )

    else:
        forecast["cloud_cover"] = 20.0
        forecast["temperature"] = (
            32.0
            + 8 * np.sin(
                (forecast["hour"] - 8) * np.pi / 12
            )
        )


   
    # Estimate solar irradiance using sunlight hours and cloud cover
    sun_profile = np.maximum(
        0,
        np.sin((forecast["hour"] - 6) * np.pi / 13),
    )

    clear_sky_irradiance = sun_profile * 1000

    cloud_factor = 1 - 0.75 * (
        forecast["cloud_cover"] / 100
    )

    forecast["solar_irradiance"] = (
        clear_sky_irradiance * cloud_factor
    ).clip(0, 1100)


    # Simulate missing temperature readings
    rng = np.random.default_rng()
    readings = forecast["temperature"].copy()

    if missing_data_pct > 0:
        missing_mask = (
            rng.random(len(readings)) < missing_data_pct / 100
        )
        readings.loc[missing_mask] = np.nan

    forecast["temperature"] = (
        readings.interpolate().ffill().bfill()
    )

    # Generate AI predictions
    forecast["pred_load_kw"] = predict_load(
        load_model,
        features,
        forecast,
    )

    forecast["pred_solar_kw"] = predict_solar(
        solar_model,
        features,
        forecast,
    )

    # Calculate overload and mitigation
    forecast = calculate_energy_balance(
        forecast,
        transformer_limit,
        battery_capacity,
        demand_response_limit=20,
    )

    return forecast
