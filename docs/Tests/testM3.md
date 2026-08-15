# Milestone 3: Create and evaluate models

## Training command

```powershell
python -c "from src.backend.db import SessionLocal; from src.backend.training import train_symbol; db=SessionLocal(); result=train_symbol(db, 'AAPL'); print('Best model:', result.best_model); print('Samples:', result.sample_count); print('Model:', result.model_path); print('Metrics:', result.metrics); db.close()"
```

## Result

```text
Best model: linear_regression
Samples: 25
Model: src/backend/training/models/AAPL_linear_regression.joblib
```

The training run compares Linear Regression, Random Forest, and Gradient Boosting using a chronological train/test split. It also records a previous-close naive baseline. On the current small AAPL dataset, the naive baseline performed better than the trained regressors, so more historical data is needed before treating the model results as meaningful.

Training metadata is saved in `src/backend/training/models/AAPL_metadata.json`, and the latest model pointer is saved in `src/backend/training/models/latest.json`.

## Notebook workflow

Notebook: [MLLSP.ipynb](../notebooks/MLLSP.ipynb)

The notebook was run successfully from the project virtual environment. All 13 Python cells completed and produced:

- AAPL price, volume, feature, and model-error graphs.
- Cleaned price, feature, and metric CSV exports under `docs/notebooks/outputs/`.
- Database validation using the project-root `mllsp.db`.
- A trained `linear_regression` model using 25 samples.

The notebook also compares the trained models with the previous-close baseline. In this run, the naive baseline had the lowest RMSE, so the results are exploratory rather than evidence of reliable predictive performance.