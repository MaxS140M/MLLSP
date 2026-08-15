# Connect to Twelve data and Validate output. 

### Input
python -c "from src.backend.ingestion import TwelveDataClient; print(TwelveDataClient().get_quote('AAPL'))"

#### OUTPUT
- Quote(symbol='AAPL', price=Decimal('305.92999'), timestamp=datetime.datetime(2026, 8, 14, 14, 30))


### Input
python -c "from src.backend.ingestion import TwelveDataClient; print(TwelveDataClient().get_quote('AAPL'))"
Quote(symbol='AAPL', price=Decimal('305python -c "from src.backend.ingestion import TwelveDataClient; q=TwelveDataClient().get_quote('AAPL'); assert q.symbol == 'AAPL'; assert q.price > 0; assert q.timestamp is not None; print('Quote valid:', q)"

#### OUTPUT
-Quote valid: Quote(symbol='AAPL', price=Decimal('305.92999'), timestamp=datetime.datetime(2026, 8, 14, 14, 30))