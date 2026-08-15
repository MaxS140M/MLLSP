# import historical prices and save them to database


#### input 
$ python -c "from src.backend.db import SessionLocal, init_db; from src.backend.ingestion import TwelveDataClient, ingest_historical_prices; init_db(); db=SessionLocal(); print('Records written:', ingest_historical_prices(db, TwelveDataClient(), 'AAPL', outputsize=5)); db.close()"

#### ouput

Records written: 5

[Database file](../../mllsp.db)

## Live quote retrieval

### Input

```powershell
python -c "from src.backend.db import SessionLocal, init_db; from src.backend.ingestion import TwelveDataClient, ingest_live_quote; init_db(); db=SessionLocal(); print('Live quote:', ingest_live_quote(db, TwelveDataClient(), 'AAPL')); db.close()"
```

### Output

```text
Live quote: Quote(symbol='AAPL', price=Decimal('305.92999'), timestamp=datetime.datetime(2026, 8, 14, 14, 30))
Saved observations: 6
```

## Rate-limit handling

The client was tested with simulated Twelve Data responses.

### Retry test

- A `429` response with `Retry-After: 0` was retried.
- The next successful response returned the quote.
- Output: `Retry test passed`

### Retry exhaustion test

- Three consecutive `429` responses were sent with `max_retries=2`.
- The client stopped retrying and raised `TwelveDataRateLimitError`.
- Output: `Exhaustion test passed`

The client also reports clear errors for request timeouts, HTTP failures, invalid JSON, and malformed provider responses.