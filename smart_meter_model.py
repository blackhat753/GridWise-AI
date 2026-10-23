
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error


def train_smart_meter_model(meter_data):
    """Train and evaluate a model on historical hourly meter energy."""

    data = meter_data.sort_values("hour").copy()

    data["hour_of_day"] = data["hour"].dt.hour
    data["day_of_week"] = data["hour"].dt.dayofweek
    data["month"] = data["hour"].dt.month

    # Previous hour's energy consumption
    data["previous_hour_kwh"] = data["energy_kwh"].shift(1)

    data = data.dropna(
        subset=[
            "energy_kwh",
            "previous_hour_kwh",
            "hour_of_day",
            "day_of_week",
            "month",
        ]
    )

    if len(data) < 30:
        raise ValueError(
            "At least 30 usable hourly readings are required."
        )

    features = [
        "hour_of_day",
        "day_of_week",
        "month",
        "previous_hour_kwh",
    ]

    split = int(len(data) * 0.8)

    if split < 20 or len(data) - split < 5:
        raise ValueError("Not enough data for a reliable test split.")

    train = data.iloc[:split]
    test = data.iloc[split:]

    model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=3,
        random_state=42,
    )

    model.fit(train[features], train["energy_kwh"])

    predictions = model.predict(test[features])

    results = test[["hour", "energy_kwh"]].copy()
    results["predicted_kwh"] = predictions.clip(min=0)

    mae = mean_absolute_error(
        results["energy_kwh"],
        results["predicted_kwh"],
    )

    return model, results, mae
