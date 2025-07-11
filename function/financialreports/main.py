import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
from io import StringIO
import os
import time
import logging
import azure.functions as func
import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
from datetime import datetime
from zoneinfo import ZoneInfo

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S' 
)

NAMESPACE_CONNECTION_STR = os.getenv("financial_report_queue_connectionstring")
QUEUE_NAME = 'financial_report_queue'
db_table = 'financial_reports_raw'

try:
    # Connect to the Azure Cosmos DB for PostgreSQL instance
    conn = psycopg2.connect(
        host=os.getenv('postgres_host'),
        port=int(os.getenv('postgres_port')),
        dbname=os.getenv('postgres_dbname'),
        user=os.getenv('postgres_user'),
        password=os.getenv('postgres_password'),
        sslmode="require"  # Cosmos DB requires SSL
    )
    logging.info("Connected to DB successfully")
except Exception as e:
    logging.exception(e)

def scrap_financial_reports(ticker: str) -> pd.DataFrame:
    # adres
    url = f"https://www.biznesradar.pl/raporty-finansowe-rachunek-zyskow-i-strat/{ticker}"
    print(url)
    # jestem przegladarką
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # GET request
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # nazwy kolumn pl: eng
    TITLES = {
        "Przychody ze sprzedaży": "sales_revenue",
        "Zysk ze sprzedaży": "gross_profit",
        "Zysk operacyjny (EBIT)": "EBIT",
        "Zysk z działalności gospodarczej": "operating_profit",
        "Zysk netto": "net_profit",
        "EBITDA": "EBITDA"
    }

    # start scrapping
    table = soup.find("table", class_="report-table")
    if not table:
        raise ValueError("Financial report table not found on page.")

    # Extract and clean year headers
    header_cells = table.find("tr").find_all("th")[1:-1]
    years = [cell.get_text(strip=True).split("(")[0] for cell in header_cells]

    # Initialize dictionary for data
    data_dict = {"year": years}

    # Extract rows matching specified titles
    for row in table.find_all("tr")[1:]:
        label_cell = row.find("td", class_="f")
        if not label_cell:
            continue

        title_pl = label_cell.get_text(strip=True)
        if title_pl in TITLES:
            title_en = TITLES[title_pl]
            # print(values)
            values = []
            for cell in row.find_all("td", class_="h"):
                # Prefer <span class="pv">, fallback to <span class="premium-value">
                span = cell.find("span", class_="pv")
                if span:
                    val = span.get_text(strip=True)
                else:
                    premium_span = cell.find("span", class_="premium-value")
                    if premium_span:
                        val = premium_span.get_text(strip=True)
                    else:
                        val = ""
                values.append(val)
            data_dict[title_en] = values

    # print(data_dict)

    # Convert to DataFrame
    df = pd.DataFrame(data_dict)  
    df = df[["year"] + list(TITLES.values())]
    # Adding ticker
    df.insert(0, 'ticker', ticker)

    return df

async def run_and_receive():
    final_df = pd.DataFrame()
    for _ in range(5):
        async with ServiceBusClient.from_connection_string(
            conn_str=NAMESPACE_CONNECTION_STR,
            logging_enable=True) as servicebus_client:

            async with servicebus_client:
                receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
                async with receiver:
                    received_msgs = await receiver.receive_messages(max_wait_time=5, max_message_count=8)
                    if len(received_msgs) == 0:
                        logging.info(f"No data received from the queue, retrying... {_ + 1}/5")
                        continue
                    for msg in received_msgs:
                        logging.info(f"Received message: {str(msg)}")
                        try:
                            df = scrap_financial_reports(str(msg))
                            logging.info(f"Scrapped for ticker: {str(msg)}")
                            final_df = pd.concat([df, final_df])
                        except KeyError:
                            logging.info(f"{str(msg)} - banking company, other financial report - skip")
                        await receiver.complete_message(msg)
                        time.sleep(30)
        logging.info(f"Inserting data to table: {db_table}")
        copy_to_table(conn, final_df, db_table)
        return

def copy_to_table(conn, df, table):
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)
    cursor = conn.cursor()
    try:
        cursor.copy_from(buffer, table, sep=',')
        conn.commit()
        logging.info(f"data inserted into {table}.")
    except Exception as e:
        conn.rollback()
        logging.exception(e)
    finally:
        cursor.close()

def main():
    asyncio.run(run_and_receive())

