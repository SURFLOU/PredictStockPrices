import logging.config
import requests 
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
import os
from dotenv import load_dotenv 
from io import StringIO
import logging 
import time 

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S' 
)

load_dotenv()

NAMESPACE_CONNECTION_STR = os.getenv("cashflow_queue_connectionstring")
QUEUE_NAME = "financial_cashflow_queue"
db_table = "financial_cashflow_raw"


def scrap_for_ticker(ticker):
    url = f"https://www.biznesradar.pl/raporty-finansowe-przeplywy-pieniezne/{ticker}"
    url_text = requests.get(url).text
    soup = BeautifulSoup(url_text, 'html.parser')

    headers = soup.find_all('th', class_='thq h')
    dates = [header.get_text(strip=True).split('(')[-1].strip(')') for header in headers]
    last_date = soup.find_all('th', class_='thq h newest')
    last_date = [last_date.get_text(strip=True).split('(')[-1].split(')')[0] for last_date in last_date]
    dates = dates + last_date

    fcf_row = soup.find('tr', {'data-field': 'CashflowFCM'})

    fcf_values = []
    for td in fcf_row.find_all('td', class_='h'):
        span = td.find('span', class_='value')
        if span:
            value_text = span.get_text(strip=True).replace(' ', '').replace('\xa0', '')
            try:
                value = int(value_text.replace('−', '-').replace(',', ''))
            except ValueError:
                value = None
        else:
            value = None
        fcf_values.append(value)

    df = pd.DataFrame({
    'ticker': ticker,
    'year': dates,
    'free_cashflow': fcf_values
    })

    return df 



async def run_and_receive():
    try: 
        conn = psycopg2.connect(
            host=os.getenv('postgres_host'),
            port=int(os.getenv('postgres_port')),
            dbname=os.getenv('postgres_dbname'),
            user=os.getenv('postgres_user'),
            password=os.getenv('postgres_password'),
            sslmode="require" 
        )
        logging.info("Connected to DB successfully")
    except Exception as e:
        logging.exception(e)
    final_df = pd.DataFrame()
    for _ in range(5):
        async with ServiceBusClient.from_connection_string(
            conn_str=NAMESPACE_CONNECTION_STR,
            logging_enable=True) as servicebus_client:

            async with servicebus_client:
                receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
                async with receiver:
                    received_msgs = await receiver.receive_messages(max_wait_time=5, max_message_count=10)
                    if len(received_msgs) == 0:
                        logging.info(f"No data received from the queue, retrying... {_ + 1}/5")
                        continue
                    for msg in received_msgs:
                        logging.info(f"Received message: {str(msg)}")
                        df = scrap_for_ticker(str(msg))
                        logging.info(f"Scrapped for ticker: {str(msg)}")
                        final_df = pd.concat([df, final_df])
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