# MLLSP Project Outline

## 1. Project Overview

MLLSP (Machine Learning Live Stocks Prediction) is a small end-to-end application for collecting stock market data, generating model features, producing short-term predictions, and presenting the results in a browser dashboard.

The first version should prioritize a reliable and understandable pipeline over model complexity. The same feature-engineering code must be used during training and prediction so that the model receives consistent inputs in both environments.

## 2. Goals

The project should provide a simple, reliable path from market data to a visible prediction.

- Collect and store historical and current stock data.
- Turn price data into reusable model features.
- Train and compare a few baseline models.
- Serve quotes and predictions through a FastAPI backend.
- Show prices, predictions, and charts in a lightweight frontend.
- Report missing data and service errors clearly.

## 3. Initial Scope

The first release is intentionally small so the full data, model, and dashboard workflow can be tested end to end.

### In scope

- A small list of configurable stock symbols.
- Twelve Data for historical and live market data.
- SQLite by default, with a configurable database URL.
- One prediction target and a documented forecast period.
- A few baseline regression models evaluated with time-ordered data.
- A static HTML and JavaScript dashboard with charts.

### Out of scope

- Automated trading or order placement.
- Financial advice or guaranteed results.
- High-frequency or tick-level trading data.
- User accounts, portfolios, or multi-user features.
- Complex deep-learning models before the baseline models are measured.


## 4. System Flow

1. The ingestion layer requests historical or live data from Twelve Data.
2. The database layer validates and stores normalized market observations.
3. The feature layer converts stored observations into model-ready inputs.
4. The training layer fits candidate models, evaluates them, and saves the best artifact.
5. The API loads the latest model for a symbol and returns quotes or predictions.
6. The frontend polls the API and renders the current result and price history.

## 5. Component Responsibilities

### Backend ingestion

Gets historical prices and live quotes from Twelve Data and prepares them for storage.

- Fetch and clean market data.
- Handle missing data, API errors, and rate limits.
- Support manual or scheduled data updates.

### Database

Stores the market data that the features, training, and API layers use.

- Define tables for symbols and price observations.
- Set up the default SQLite database.
- Allow the database location to be changed with `DATABASE_URL`.

### Feature engineering

Turns stored prices into the inputs used by the model.

- Calculate returns, lagged prices, and rolling statistics.
- Check that enough history is available.
- Share the same feature functions with training and prediction.

### Training

Builds and saves the model used for predictions.

- Create time-ordered training and test data.
- Compare baseline models and record their results.
- Save the best model and its metadata in `training/models/`.

### API

Connects the frontend to market data and saved models.

- Provide health, quote, and prediction endpoints.
- Validate requests and return clear errors.
- Load the correct model for each supported symbol.

### Frontend

Shows the latest market information and model results in the browser.

- Display supported symbols, current prices, and predictions.
- Render price history in a chart.
- Show loading, empty, and error states.

## 6. Delivery Milestones

### Milestone 1: Set up the project  // completed

- Configure dependencies and environment variables.
- Set up the database and core tables.
- Connect to Twelve Data and validate its responses.

### Milestone 2: Build the data pipeline

- Import historical prices and save them to the database.
- Add live quote retrieval.
- Handle rate limits and basic errors.

### Milestone 3: Create and evaluate models

- Create shared features for training and prediction.
- Train baseline models using time-ordered data.
- Save the best model and its evaluation results.

### Milestone 4: Add the prediction API

- Add health, quote, and prediction routes.
- Load saved models and validate requests.
- Test valid requests and common data errors.

### Milestone 5: Connect and verify the dashboard

- Connect the frontend to the API.
- Add quote, prediction, chart, loading, and error states.
- Test the complete local workflow and document setup.

## 7. Success Criteria

- A clean setup can initialize the database and run the backend locally.
- Historical data can be ingested and queried without malformed records.
- Training and inference use the same feature definitions.
- A saved model can be loaded to return a prediction for supported data.
- API responses are documented and provide actionable errors.
- The dashboard renders live data or an honest unavailable/error state.
- Tests cover ingestion normalization, feature calculations, model loading, and key API routes.

## 8. Risks and Decisions to Track

- Twelve Data availability, quotas, and symbol naming may constrain refresh frequency.
- Stock prices are non-stationary; evaluation must use chronological splits and avoid leakage.
- A prediction should include its timestamp, forecast horizon, and model version.
- Missing or stale data must be surfaced rather than silently presented as current.
- Baseline metrics should be compared with a simple naive forecast before selecting a model.
- Results are experimental predictions, not financial advice.
