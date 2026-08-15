# Milestone 5: Connect and verify the dashboard

## Start both services

From the repository root, with the virtual environment active:

```powershell
uvicorn src.backend.api.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
python -m http.server 5500 --directory src/Frontend
```

Open the dashboard at `http://127.0.0.1:5500`.

## Dashboard behavior

- Checks the API health route and shows the connection state.
- Lets the user switch between AAPL and MSFT.
- Loads live quote data from `/quote/{symbol}`.
- Loads the saved-model prediction from `/predict/{symbol}`.
- Loads stored closing prices from `/history/{symbol}`.
- Renders the price history with Chart.js.
- Shows loading, empty-chart, and API error states.
- Supports a manual refresh button.

## Verification

The local browser check confirmed:

```text
API online
Microsoft Corporation / MSFT
Current quote: $495.40
Prediction: $494.89
Historical points: 30
```

The dashboard is responsive and uses the API's CORS configuration for local frontend requests.