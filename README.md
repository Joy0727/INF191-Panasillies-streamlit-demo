# INF191 Panasillies Streamlit Demo

Streamlit-only frontend for the OneMedia3 campaign optimization demo.

This repository intentionally does not include backend data files or model artifacts. Point the app to the local backend data folder with `PANASILLIES_DATA_DIR`.

## Run

```bash
pip install -r requirements.txt
PANASILLIES_DATA_DIR=<path-to-backend-data-folder> python3 run.py
```

Then open the URL shown by Streamlit.

Example:

```bash
PANASILLIES_DATA_DIR=../INF191-Panasillies python3 run.py
```

Demo login:

```text
Email: panasillies.user@panasonic.aero
Password: password
```

## Data Used

The app reads, but does not modify:

- `output_zone_forecasts.csv`
- `campaigns_cleaned.csv`
- `campaign_delivery.csv`
- `output_pacing.csv`
- `output_alerts.csv`
- `output_allocations.csv`
- `output_feasibility.csv`
- `output_priority_scores.csv`
- `output_zone_utilization.csv`
- `fleet_metrics.csv`

New campaign demo state is stored in browser local storage only.
