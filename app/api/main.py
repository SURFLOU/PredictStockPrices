from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
from typing import List
import datetime

app = FastAPI()

def connect_to_db():
    conn = psycopg2.connect(
        dbname="airflow",
        user="airflow",
        password="airflow",
        host="postgres"
    )
    cursor = conn.cursor()
    return cursor, conn

class StockPrice(BaseModel):
    stock_ticker: str
    stock_price: float
    stock_update_date: datetime.date

@app.get("/stocks/{symbol}")
def get_stock_price(symbol: str):
    cursor, conn = connect_to_db()
    query = f"SELECT stock_ticker, stock_price, stock_update_date FROM StockDailyPrices WHERE stock_ticker = '{symbol}' ORDER BY stock_update_date DESC LIMIT 1"
    cursor.execute(query)
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"stock_ticker": row[0], "stock_price": row[1], "stock_update_date": row[2].strftime("%Y-%m-%d")}
    return {"error": "Stock symbol not found"}

@app.get("/historical/{symbol}")
def get_historical_stock_data(symbol: str):
    cursor, conn = connect_to_db()
    query = f"SELECT stock_ticker, stock_price, stock_update_date FROM StockDailyPrices WHERE stock_ticker = '{symbol}' ORDER BY stock_update_date"
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    historical_data = [
        {"stock_ticker": row[0], "stock_price": row[1], "stock_update_date": row[2].strftime("%Y-%m-%d")}
        for row in rows
    ]
    return {"historical_data": historical_data}

@app.post("/scrape/start")
def start_scraping():
    return {"status": "scraping started"}

@app.get("/gettickers", response_model=List[str])
def get_all_tickers():
    cursor, conn = connect_to_db()
    query = "SELECT DISTINCT stock_ticker FROM StockNames"
    cursor.execute(query)
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return sorted(tickers)

@app.get("/getstockname/{symbol}")
def get_stock_name(symbol: str):
    cursor, conn = connect_to_db()
    query = "SELECT sn.stock_name FROM StockNames sn JOIN StockDailyPrices sdp ON sn.stock_ticker = sdp.stock_ticker"
    cursor.execute(query)
    stock_name = cursor.fetchall()[0]
    conn.close()
    return stock_name
