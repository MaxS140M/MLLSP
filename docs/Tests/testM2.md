# import historical prices and save them to database


#### input 
$ python -c "from src.backend.db import SessionLocal, init_db; from src.backend.ingestion import TwelveDataClient, ingest_historical_prices; init_db(); db=SessionLocal(); print('Records written:', ingest_historical_prices(db, TwelveDataClient(), 'AAPL', outputsize=5)); db.close()"

#### ouput

Records written: 5

[seen here](../../mllsp.db)