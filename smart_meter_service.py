
import pandas as pd


def load_smart_meter_data(source, chunksize=500_000):
    """Load large smart-meter CSV files and aggregate readings hourly."""

    required = [
        "x_Timestamp",
        "t_kWh",
        "z_Avg Voltage (Volt)",
        "z_Avg Current (Amp)",
        "y_Freq (Hz)",
        "meter",
    ]

    hourly_parts = []

    for chunk in pd.read_csv(source, chunksize=chunksize):
        missing = [col for col in required if col not in chunk.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        chunk["x_Timestamp"] = pd.to_datetime(
            chunk["x_Timestamp"], errors="coerce"
        )

        numeric_cols = [
            "t_kWh",
            "z_Avg Voltage (Volt)",
            "z_Avg Current (Amp)",
            "y_Freq (Hz)",
        ]

        for col in numeric_cols:
            chunk[col] = pd.to_numeric(chunk[col], errors="coerce")

        chunk = chunk.dropna(
            subset=["x_Timestamp", "t_kWh", "meter"]
        )

        chunk["hour"] = chunk["x_Timestamp"].dt.floor("h")

        grouped = chunk.groupby(["meter", "hour"]).agg(
            energy_kwh=("t_kWh", "sum"),
            voltage_sum=("z_Avg Voltage (Volt)", "sum"),
            voltage_count=("z_Avg Voltage (Volt)", "count"),
            current_sum=("z_Avg Current (Amp)", "sum"),
            current_count=("z_Avg Current (Amp)", "count"),
            frequency_sum=("y_Freq (Hz)", "sum"),
            frequency_count=("y_Freq (Hz)", "count"),
        )

        hourly_parts.append(grouped)

    if not hourly_parts:
        raise ValueError("No valid smart-meter readings found.")

    result = pd.concat(hourly_parts).groupby(
        level=["meter", "hour"]
    ).sum()

    result["avg_voltage"] = (
        result["voltage_sum"] / result["voltage_count"].replace(0, float("nan"))
    )
    result["avg_current"] = (
        result["current_sum"] / result["current_count"].replace(0, float("nan"))
    )
    result["avg_frequency"] = (
        result["frequency_sum"] / result["frequency_count"].replace(0, float("nan"))
    )

    return result.reset_index()
