# GridWise AI — Starter Prototype

This is a hackathon-ready demonstration of AI-based load forecasting and demand response.

## Features
- Synthetic hourly electricity-demand data
- Random Forest model trained on generated demo data
- Sunny / cloudy / heavy-rain scenario selector
- Estimated rooftop solar generation
- Estimated battery contribution
- Transformer loading indicator and alert
- 24-hour chart and action recommendations

## Run in VS Code

1. Install Python 3.10 or newer.
2. Extract this ZIP and open the `GridWise_AI_Starter` folder in VS Code.
3. Open the VS Code terminal in that folder.
4. Create a virtual environment (recommended):

   Windows:
   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   ```

5. Install packages:
   ```bash
   pip install -r requirements.txt
   ```

6. Start the app:
   ```bash
   streamlit run app.py
   ```

7. A browser tab should open with the GridWise AI dashboard.

## Important
The dataset is synthetic and the model is trained on generated data only. This is a demonstration, not a validated utility forecasting model. Replace synthetic data with historical utility measurements and validate the model before making real-world claims. Do not connect this prototype directly to live grid controls.
