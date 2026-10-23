
import numpy as np
import pandas as pd


def generate_training_data(n_days=30):
    """Generate synthetic hourly electricity and weather data."""

    if n_days < 1:
        raise ValueError("n_days must be at least 1.")

    rng = np.random.default_rng(42)

    dates = pd.date_range(
        end=pd.Timestamp.now().floor("h"),
        periods=n_days * 24,
        freq="h"
    )

    df = pd.DataFrame({"timestamp": dates})

    # Calendar features
    df["hour"] = df["timestamp"].dt.hour
    df["dayofweek"] = df["timestamp"].dt.dayofweek
    df["is_weekend"] = df["dayofweek"].isin([5, 6]).astype(int)
    df["sin_hour"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["cos_hour"] = np.cos(2 * np.pi * df["hour"] / 24)

    # Weather features
    df["temperature"] = (
        18
        + 10 * np.sin((df["hour"] - 8) * np.pi / 12)
        + rng.normal(0, 1.5, len(df))
    )

    df["cloud_cover"] = np.clip(
        rng.beta(2, 5, len(df)) * 100
        + rng.normal(0, 5, len(df)),
        0,
        100
    )

    # Solar generation
    sun_profile = np.maximum(
        0,
        np.sin((df["hour"] - 6) * np.pi / 13)
    )

    df["solar_irradiance"] = (
        sun_profile * 1000 * (1 - df["cloud_cover"] / 130)
        + rng.normal(0, 20, len(df))
    )

    df["solar_irradiance"] = df["solar_irradiance"].clip(0, 1100)

    df["solar_gen_kw"] = (
        df["solar_irradiance"]
        * 0.12
        * (1 - 0.004 * (df["temperature"] - 25))
    ).clip(lower=0)

    # Gross feeder demand
    morning_peak = np.exp(-((df["hour"] - 9) ** 2) / 8) * 80
    evening_peak = np.exp(-((df["hour"] - 19) ** 2) / 10) * 120

    base_load = 90 + (df["temperature"] - 18) * 2.5

    df["gross_load_kw"] = (
        base_load
        + morning_peak
        + evening_peak
        + rng.normal(0, 5, len(df))
    )

    return df
