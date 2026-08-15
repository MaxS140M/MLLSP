# MLLSP
Machine Learning Live Stocks Prediction

## Technology stack

- **Backend:** Python, FastAPI, Uvicorn
- **Database:** SQLite with SQLAlchemy
- **Data processing:** pandas and NumPy
- **Machine learning:** scikit-learn and joblib
- **Market data:** Twelve Data API
- **Frontend:** Static HTML and JavaScript

## Documentation

- [Setup guide](docs/setup.md)
- [Project outline](docs/project_outline.md)
- [Project structure](docs/project_structure.md)
- [Milestones](docs/milestones.md)
- [Milestone 1 test notes](docs/Tests/testM1.md)
- [Milestone 2 test notes](docs/Tests/testM2.md)
- [Milestone 3 test notes](docs/Tests/testM3.md)
- [Milestone 3 analysis notebook](docs/notebooks/MLLSP.ipynb)

## Workflow 

Twelve Data API
    ↓
ingest_historical_prices("MSFT")
    ↓
mllsp.db
    ↓
MLLSP.ipynb reads MSFT data
    ↓
features are created
    ↓
models are trained and evaluated
    ↓
model files and metadata are saved
    ↓
frontend not added yet.
    ↓

    ↓

    ↓