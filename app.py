
import streamlit as st
import plotly.graph_objects as go

from controller import run_forecast


st.set_page_config(
    page_title="AI Grid Load & DR Platform",
    layout="wide",
)


def main():
    st.title("⚡ AI-Based Load Forecasting & Demand Response Platform")

    # Sidebar controls
    st.sidebar.header("⚙️ Simulation Controls")

    transformer_limit = st.sidebar.slider(
        "Transformer Safe Capacity (kW)",
        min_value=120,
        max_value=220,
        value=150,
        step=5,
    )

    battery_capacity = st.sidebar.slider(
        "Available Battery Power (kW)",
        min_value=0,
        max_value=80,
        value=40,
        step=5,
    )

    weather_cond = st.sidebar.selectbox(
        "Weather Scenario",
        [
            "Real Weather Forecast (Bengaluru)",
            "Sunny Day",
            "Cloudy Afternoon (Solar Drop)",
            "Sudden Evening Heatwave",
        ],
    )

    missing_data_pct = st.sidebar.slider(
        "Simulate Missing Meter Data (%)",
        min_value=0,
        max_value=30,
        value=15,
        step=5,
    )

    # Run forecasting pipeline
    try:
        forecast = run_forecast(
            transformer_limit=transformer_limit,
            battery_capacity=battery_capacity,
            weather_cond=weather_cond,
            missing_data_pct=missing_data_pct,
        )
    except (ValueError, KeyError) as error:
        st.error(f"Unable to generate forecast: {error}")
        return

    # Calculate dashboard metrics
    has_overload = forecast["overload_kw"].max() > 0
    remaining_overload = forecast["unresolved_overload_kw"].max()
    final_battery_soc = forecast["battery_soc_pct"].iloc[-1]
    final_battery_energy = forecast["battery_energy_remaining_kwh"].iloc[-1]
    peak_reduction = max(
        0,
        (
            forecast["net_load_kw"]
            - forecast["mitigated_net_load_kw"]
        ).max(),
    )

    total_shifted_energy = (
        forecast["battery_dispatch_kw"]
        + forecast["demand_response_kw"]
    ).sum()

    # Illustrative savings estimate
    estimated_savings = (
        peak_reduction * 15
        + total_shifted_energy * 0.15
    )

    # Grid status alert
    if remaining_overload > 0:
        st.error(
            f"🚨 **OVERLOAD RISK REMAINS:** "
            f"{remaining_overload:.1f} kW of overload remains "
            "after the simulated mitigation actions."
        )
    elif has_overload:
        st.warning(
            "⚠️ **OVERLOAD PREDICTED BEFORE MITIGATION:** "
            "The simulated battery and demand response cover "
            "the predicted overload. Real-world effectiveness "
            "must be verified."
        )
    else:
        st.success(
            "✅ **GRID STATUS NORMAL:** "
            "Forecast net load is within transformer limits."
        )

    # KPI metrics
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Max Demand Forecast",
        f"{forecast['pred_load_kw'].max():.1f} kW",
    )

    c2.metric(
        "Max Solar Generation",
        f"{forecast['pred_solar_kw'].max():.1f} kW",
    )

    c3.metric(
        "Peak Reduction",
        f"{peak_reduction:.1f} kW",
    )

    c4.metric(
        "Estimated Cost Savings",
        f"${estimated_savings:,.2f}",
    )

    st.markdown("---")

    # Battery monitoring
    st.subheader("🔋 Battery Monitoring")

    b1, b2, b3 = st.columns(3)

    b1.metric(
        "Battery Charge Remaining",
        f"{final_battery_soc:.1f}%",
    )

    b2.metric(
        "Remaining Battery Energy",
        f"{final_battery_energy:.1f} kWh",
    )

    b3.metric(
        "Battery Energy Capacity",
        "100 kWh",
    )

    st.caption(
        "Simulated battery capacity: 100 kWh; "
        "minimum state of charge: 20%."
    )
        # Battery state-of-charge chart
    battery_fig = go.Figure()

    battery_fig.add_trace(
        go.Scatter(
            x=forecast["timestamp"],
            y=forecast["battery_soc_pct"],
            mode="lines+markers",
            name="Battery Charge (%)",
            line=dict(color="#2ecc71", width=3),
        )
    )

    battery_fig.add_hline(
        y=20,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text="Minimum Charge: 20%",
    )

    battery_fig.update_layout(
        title="Battery State of Charge — 24 Hours",
        xaxis_title="Time",
        yaxis_title="Battery Charge (%)",
        yaxis=dict(range=[0, 100]),
        height=350,
        hovermode="x unified",
    )

    st.plotly_chart(battery_fig, width="stretch")

    if final_battery_soc <= 20:
        st.warning(
            "⚠️ Battery has reached its minimum permitted charge."
        )
     
    st.markdown("---")
    
 
    # Battery usage scenario comparison
    st.subheader("🔋 Battery Usage & Lifespan Variance")

    st.caption(
        "Illustrative estimate only. Assumes 3,000 equivalent full "
        "cycles to end of useful cycle life. Actual lifespan depends "
        "on battery chemistry, temperature, depth of discharge, "
        "charging behaviour, and manufacturer specifications. "
        "Calendar ageing is not included."
    )

    assumed_cycle_life = 3000

    usage_scenarios = {
        "Light usage": 0.5,
        "Moderate usage": 1.0,
        "Heavy usage": 2.0,
    }

    scenario_results = []

    for scenario, cycles_per_day in usage_scenarios.items():
        annual_cycles = cycles_per_day * 365
        estimated_years = assumed_cycle_life / annual_cycles

        scenario_results.append(
            {
                "Usage Scenario": scenario,
                "Equivalent Cycles per Day": cycles_per_day,
                "Estimated Cycles per Year": round(annual_cycles),
                "Illustrative Cycle-Based Life (Years)": round(
                    estimated_years, 1
                ),
            }
        )

    st.dataframe(
        scenario_results,
        use_container_width=True,
        hide_index=True,
    )

    # Forecast chart and mitigation panel
    col_chart, col_actions = st.columns([3, 1])

    with col_chart:
        st.subheader("📈 24-Hour Ahead Forecast")

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=forecast["timestamp"],
                y=forecast["pred_load_kw"],
                mode="lines",
                name="Gross Load (kW)",
                line=dict(color="#2980b9", width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=forecast["timestamp"],
                y=forecast["pred_solar_kw"],
                mode="lines",
                name="Solar Generation (kW)",
                line=dict(
                    color="#f39c12",
                    width=2,
                    dash="dot",
                ),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=forecast["timestamp"],
                y=forecast["net_load_kw"],
                mode="lines",
                name="Net Load Before Mitigation (kW)",
                line=dict(color="#8e44ad", width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=forecast["timestamp"],
                y=forecast["mitigated_net_load_kw"],
                mode="lines",
                name="Net Load After Mitigation (kW)",
                line=dict(color="#27ae60", width=3),
            )
        )

        fig.add_hline(
            y=transformer_limit,
            line_dash="dash",
            line_color="#e74c3c",
            annotation_text=(
                f"Transformer Limit: {transformer_limit} kW"
            ),
        )

        fig.update_layout(
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

        st.plotly_chart(fig, width="stretch")

    # Automated mitigation panel
    with col_actions:
        st.subheader("🛡️ Automated Mitigation")

        st.write(
            f"**Transformer Limit:** {transformer_limit} kW"
        )

        st.write(
            f"**Battery Power Limit:** {battery_capacity} kW"
        )

        max_battery = forecast["battery_dispatch_kw"].max()
        max_dr = forecast["demand_response_kw"].max()

        st.markdown("#### Mitigation Actions")

        if has_overload:
            st.write(
                f"🔋 Battery dispatch: **{max_battery:.1f} kW**"
            )

            st.write(
                f"📡 Demand response: **{max_dr:.1f} kW**"
            )

            if remaining_overload > 0:
                st.warning(
                    f"Remaining overload: "
                    f"{remaining_overload:.1f} kW"
                )
            else:
                st.success(
                    "Simulated overload fully mitigated."
                )
        else:
            st.success("No mitigation required.")

        st.markdown("---")

        st.caption(
            f"Missing-data simulation: {missing_data_pct}%. "
            "Missing temperature readings are interpolated."
        )

    # Disclaimer
    st.caption(
        "Demo note: Forecasts use synthetic data. "
        "Savings are illustrative estimates, not guaranteed savings."
    )


if __name__ == "__main__":
    main()
