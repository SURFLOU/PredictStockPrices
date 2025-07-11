import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import psycopg2
import numpy as np
from io import StringIO
import logging
import os 

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S' 
)

urls = [
    "https://www.biznesradar.pl/spolki-wskazniki-wartosci-rynkowej/akcje_gpw,1,CWKCurrent",
    "https://www.biznesradar.pl/spolki-wskazniki-wartosci-rynkowej/akcje_gpw,1,CWKGrahamCurrent",
    "https://www.biznesradar.pl/spolki-wskazniki-wartosci-rynkowej/akcje_gpw,1,CPCurrent",
    "https://www.biznesradar.pl/spolki-wskazniki-wartosci-rynkowej/akcje_gpw,1,CZCurrent",
    "https://www.biznesradar.pl/spolki-wskazniki-wartosci-rynkowej/akcje_gpw,1,CZOCurrent",
    "https://www.biznesradar.pl/spolki-wskazniki-wartosci-rynkowej/akcje_gpw,1,EVPCurrent",
    "https://www.biznesradar.pl/spolki-wskazniki-wartosci-rynkowej/akcje_gpw,1,EVEBITCurrent",
    "https://www.biznesradar.pl/spolki-wskazniki-wartosci-rynkowej/akcje_gpw,1,EVEBITDACurrent"
]

def copy_dataframe_to_db(df, connection_params, table_name="financial_ratios"):
    column_mapping = {
        "Cena / Wartość księgowa": "price_book_value",
        "Cena / Wartość księgowa Grahama": "price_graham_book_value",
        "Cena / Przychody ze sprzedaży": "price_sales",
        "Cena / Zysk": "price_earnings",
        "Cena / Zysk operacyjny": "price_operating_profit",
        "EV / Przychody ze sprzedaży": "ev_sales",
        "EV / EBIT": "ev_ebit",
        "EV / EBITDA": "ev_ebitda"
    }

    df = df.rename(columns=column_mapping)

    required_columns = ["ticker"] + list(column_mapping.values())

    for col in required_columns:
        if col not in df.columns:
            df[col] = np.nan

    df = df[required_columns]

    df = df.where(pd.notnull(df), None)

    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False, sep=',')
    buffer.seek(0)

    try:
        conn = psycopg2.connect(**connection_params)
        logging.info("Connected to the database successfully.")
    except Exception as e:
        logging.error(f"Error while trying to connect to database: {e}")
        return
    cursor = conn.cursor()
    try:
        cursor.copy_from(buffer, table_name, sep=',', null='')
        conn.commit()
        logging.info(f"Data inserted into table '{table_name}'.")
    except Exception as e:
        conn.rollback()
        logging.exception("Error while inserting data using copy_from:", exc_info=e)
    finally:
        cursor.close()
        conn.close()


def scrape_table(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")

    headers = table.find("thead").find_all("th")
    col_name = headers[2].get_text(strip=True)

    tickers = []
    values = []

    for row in table.tbody.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 3:
            ticker_full = cols[0].text.strip()
            ticker = ticker_full.split(" ")[0]
            value_text = cols[2].get_text(strip=True).replace(" ", "").replace(",", ".")
            try:
                value = float(value_text)
            except:
                value = None

            tickers.append(ticker)
            values.append(value)

    return pd.DataFrame({"ticker": tickers, col_name: values})

def main():
    merged_df = None
    connection_params = {
    "host": os.getenv("postgres_host"),
    "port": int(os.getenv("postgres_port", "5432")),
    "dbname": os.getenv("postgres_dbname"),
    "user": os.getenv("postgres_user"),
    "password": os.getenv("postgres_password"),
    "sslmode": "require",
}

    for i, url in enumerate(urls):
        df = scrape_table(url)

        if merged_df is None:
            merged_df = df
        else:
            merged_df = pd.merge(merged_df, df, on="ticker", how="outer")

        logging.info(f"{i+1}/{len(urls)} scrapped")
        if i < len(urls) - 1:
            time.sleep(30)

    copy_dataframe_to_db(merged_df, connection_params)