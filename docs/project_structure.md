# Project Folder Structure

This document outlines the planned folder structure for **MLLSP** (Machine Learning Live Stocks Prediction).

MLLSP/
├── backend/
│   ├── ingestion/          # Scheduled data pulls from Twelve Data API
│   │   └── __init__.py
│   ├── db/                 # SQLAlchemy models + DB init scripts
│   │   └── __init__.py
│   ├── features/            # Shared feature engineering (used by training + serving)
│   │   └── __init__.py
│   ├── training/            # Offline training scripts + saved model artifacts
│   │   ├── models/          # Saved .pkl models + latest.json pointer files
│   │   │   └── .gitkeep
│   │   └── __init__.py
│   ├── api/                 # FastAPI app serving live quotes + predictions
│   │   └── __init__.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html            # Dashboard entry point
│   └── app.js                 # Frontend logic (fetch live data + predictions, render chart)
│
├── README.md
├── STRUCTURE.md               # This file
└── .gitignore


Folder	Purpose

#### backend/ingestion	
- Pulls historical (/time_series) and live (/quote) data from Twelve Data, respecting the free-tier rate limit (8 requests/minute), and stores it in the database.

####backend/db	
- Database models (SQLAlchemy) and setup scripts. Defaults to SQLite (mllsp.db), swappable via DATABASE_URL env var.

####backend/features	
- Feature engineering functions (returns, lagged features, rolling volatility/correlation) shared identically between training and serving to avoid train/serve skew.

####backend/training	
- Scripts to train and compare regressors (Linear, Random Forest, Gradient Boosting), evaluate them, and save the best model + a latest.json pointer per symbol pair.

####backend/api	
- FastAPI app exposing /health, /quote/{symbol}, and /predict endpoints.

####frontend	
- Lightweight static dashboard (no build step) that polls the API and displays live prices, predictions, and a price chart via Chart.js.