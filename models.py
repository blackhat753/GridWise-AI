
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor


FEATURE_COLUMNS = [
    "hour",
    "dayofweek",
    "is_weekend",
    "sin_hour",
    "cos_hour",
    "temperature",
    "cloud_cover",
    "solar_irradiance",
]


def train_models(training_data):
    """Train separate models for demand and solar generation."""

    required_columns = FEATURE_COLUMNS + [
        "gross_load_kw",
        "solar_gen_kw",
    ]

    missing = [
        column
        for column in required_columns
        if column not in training_data.columns
    ]

    if missing:
        raise ValueError(
            f"Training data is missing columns: {missing}"
        )

    X = training_data[FEATURE_COLUMNS]

    load_model = GradientBoostingRegressor(
        n_estimators=50,
        max_depth=4,
        random_state=42,
    )
    load_model.fit(X, training_data["gross_load_kw"])

    solar_model = GradientBoostingRegressor(
        n_estimators=50,
        max_depth=4,
        random_state=42,
    )
    solar_model.fit(X, training_data["solar_gen_kw"])

    return load_model, solar_model, FEATURE_COLUMNS.copy()


def predict_load(model, features, forecast_data):
    """Predict gross electricity demand in kW."""

    predictions = model.predict(forecast_data[features])
    return np.maximum(predictions, 0)


def predict_solar(model, features, forecast_data):
    """Predict solar generation in kW."""

    predictions = model.predict(forecast_data[features])
    return np.maximum(predictions, 0)
