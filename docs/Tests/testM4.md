# Milestone 4: Add the prediction API

## Start the API

From the repository root, with the virtual environment active:

```powershell
uvicorn src.backend.api.main:app --reload
```

The API is available at `http://127.0.0.1:8000`.

## Routes

### Health

```text
GET /health
```

Returns:

```json
{"status": "ok"}
```

### Prediction

```text
GET /predict/AAPL
```

Example response:

```json
{
  "symbol": "AAPL",
  "company": "Apple Inc.",
  "current_price": "305.929990",
  "predicted_price": 312.0335990113955,
  "model": "linear_regression",
  "horizon": 1,
  "as_of": "2026-08-14T14:30:00"
}
```

### Error handling

- Unknown symbols return `404`.
- Missing model metadata returns `404`.
- Missing model files return `404`.
- Insufficient observations return `422`.
- Provider failures from the live quote route return `502`.

## Verification

The FastAPI `TestClient` verified:

```text
health: 200 {'status': 'ok'}
prediction: 200
missing: 404 {'detail': 'No data found for UNKNOWN'}
```