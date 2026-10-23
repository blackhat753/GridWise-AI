
import numpy as np


def calculate_energy_balance(
    forecast_data,
    transformer_limit,
    battery_capacity,
    demand_response_limit=20,
    battery_energy_capacity_kwh=100,
    initial_soc_pct=100,
    min_soc_pct=20,
    discharge_efficiency=0.95,
):
    """
    Calculate grid overload mitigation and track battery energy
    for each hourly forecast step.

    battery_capacity: Maximum battery discharge power in kW.
    battery_energy_capacity_kwh: Total stored-energy capacity in kWh.
    """

    result = forecast_data.copy()

    # Validate inputs
    if transformer_limit <= 0:
        raise ValueError("Transformer limit must be positive.")

    if battery_capacity < 0:
        raise ValueError("Battery power limit cannot be negative.")

    if demand_response_limit < 0:
        raise ValueError("Demand response limit cannot be negative.")

    if battery_energy_capacity_kwh <= 0:
        raise ValueError("Battery energy capacity must be positive.")

    if not 0 <= min_soc_pct <= initial_soc_pct <= 100:
        raise ValueError(
            "SOC must satisfy 0 <= minimum SOC <= initial SOC <= 100."
        )

    if not 0 < discharge_efficiency <= 1:
        raise ValueError("Discharge efficiency must be greater than 0 and at most 1.")

    required_columns = ["pred_load_kw", "pred_solar_kw"]
    missing = [
        column for column in required_columns
        if column not in result.columns
    ]
    if missing:
        raise ValueError(f"Forecast data is missing columns: {missing}")

    # Net demand after solar generation
    result["net_load_kw"] = np.maximum(
        result["pred_load_kw"] - result["pred_solar_kw"],
        0,
    )

    # Overload before mitigation
    result["overload_kw"] = np.maximum(
        result["net_load_kw"] - transformer_limit,
        0,
    )

    # Track the battery's stored energy over time
    energy_kwh = (
        battery_energy_capacity_kwh * initial_soc_pct / 100
    )
    minimum_energy_kwh = (
        battery_energy_capacity_kwh * min_soc_pct / 100
    )

    battery_dispatch = []
    battery_energy_remaining = []
    battery_soc = []

    # Each row represents one hour in the current forecast
    for overload in result["overload_kw"]:
        available_energy_kwh = max(
            0,
            energy_kwh - minimum_energy_kwh,
        )

        # Available energy determines the maximum discharge
        # possible during this one-hour interval.
        energy_limited_power_kw = (
            available_energy_kwh * discharge_efficiency
        )

        dispatch_kw = min(
            overload,
            battery_capacity,
            energy_limited_power_kw,
        )

        # Account for discharge losses
        energy_used_kwh = dispatch_kw / discharge_efficiency
        energy_kwh = max(
            minimum_energy_kwh,
            energy_kwh - energy_used_kwh,
        )

        battery_dispatch.append(dispatch_kw)
        battery_energy_remaining.append(energy_kwh)
        battery_soc.append(
            100 * energy_kwh / battery_energy_capacity_kwh
        )

    result["battery_dispatch_kw"] = battery_dispatch
    result["battery_energy_remaining_kwh"] = battery_energy_remaining
    result["battery_soc_pct"] = battery_soc

    # Overload remaining after battery support
    result["remaining_overload_kw"] = np.maximum(
        result["overload_kw"] - result["battery_dispatch_kw"],
        0,
    )

    # Demand response has a maximum power limit
    result["demand_response_kw"] = np.minimum(
        result["remaining_overload_kw"],
        demand_response_limit,
    )

    # Overload that neither action resolves
    result["unresolved_overload_kw"] = np.maximum(
        result["remaining_overload_kw"]
        - result["demand_response_kw"],
        0,
    )

    # Net demand after mitigation
    result["mitigated_net_load_kw"] = np.maximum(
        result["net_load_kw"]
        - result["battery_dispatch_kw"]
        - result["demand_response_kw"],
        0,
    )

    return result
