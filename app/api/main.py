from fastapi import HTTPException, status, Security, FastAPI
from fastapi.security import APIKeyHeader, APIKeyQuery
from sqlalchemy import create_engine, select, Table, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from pydantic import BaseModel
import psycopg2
from typing import List
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

api_key_query = APIKeyQuery(name="api-key", auto_error=False)
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)
API_KEY = os.getenv('API_KEY')
def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
) -> str:
    if api_key_query == API_KEY:
        return api_key_query
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )
app = FastAPI()

database_url = os.getenv('DB_URL')
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

metadata = MetaData()


stock_names = Table("stocknames", metadata, autoload_with=engine)
stock_daily_prices = Table("stockdailyprices", metadata, autoload_with=engine)

class StockModel(BaseModel):
    stock_ticker: str
    stock_price: float
    stock_update_date: datetime.date
    stock_name: str

@app.get("/stocks/{symbol}")
def get_stock_price(symbol: str, api_key: str = Security(get_api_key)):
    db = engine.connect()
    result = db.execute(select(stock_daily_prices.c.stock_ticker, stock_daily_prices.c.stock_price, stock_daily_prices.c.stock_update_date)
                        .where(stock_daily_prices.c.stock_ticker == symbol))
    row = result.fetchone()
    if row:
        return {"stock_ticker": row[0], "stock_price": row[1], "stock_update_date": row[2].strftime("%Y-%m-%d")}
    raise HTTPException(status_code=404, detail="Stock symbol not found")

@app.get("/historical/{symbol}")
def get_historical_stock_data(symbol: str, api_key: str = Security(get_api_key)):
    db = engine.connect()
    result = db.execute(select(stock_daily_prices.c.stock_ticker, stock_daily_prices.c.stock_price, stock_daily_prices.c.stock_update_date)
                        .where(stock_daily_prices.c.stock_ticker == symbol.upper())
                        .order_by(stock_daily_prices.c.stock_update_date))
    
    historical_data = [
        {"stock_ticker": row[0], "stock_price": row[1], "stock_update_date": row[2].strftime("%Y-%m-%d")}
        for row in result
    ]
    return {"historical_data": historical_data}

@app.post("/scrape/start")
def start_scraping():
    return {"status": "scraping started"}

@app.get("/gettickers", response_model=List[str])
def get_all_tickers(api_key: str = Security(get_api_key)):
    db = engine.connect()
    result = db.execute(select(stock_names.c.stock_ticker))
    tickers = [row[0] for row in result]
    return sorted(tickers)

@app.get("/getstockname/{symbol}")
def get_stock_name(symbol: str):
    db = engine.connect()
    result = db.execute(select(stock_names.c.stock_name).where(stock_names.c.stock_ticker == symbol))
    row = result.fetchone()
    if row:
        return row[0]
    raise HTTPException(status_code=404, detail="Stock symbol not found")
