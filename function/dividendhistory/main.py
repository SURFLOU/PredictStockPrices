import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os
import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage
import time
from io import StringIO
import logging 


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S' 
)

load_dotenv()
NAMESPACE_CONNECTION_STR = os.getenv('dividend_queue_connectionstring')
QUEUE_NAME = "dividend_queue"


def page_data(ticker):
    html = requests.get(f'https://www.biznesradar.pl/dywidenda/{ticker}', verify=False).text
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    dataset = []
    
    
    for row in table.find_all('tr')[1:]:
        columns = row.find_all(['td'])
        data = [col.get_text(strip=True) for col in columns]
        count = sum(len(str(x)) <= 1 for x in data)
        
        if data and len(data) == 10 and count < 8:
            data = [ticker] + data
            dataset.append(data)
            yield data


def clean_data(df):
    df_clean = df[[0,1,3,4,10]].copy()
    df_clean.columns = ['ticker','dividend_year','dividend_per_share','dividend_value','payment_date']
    df_clean['dividend_value'] = df_clean['dividend_value'].replace(" ", "", regex=True)
    df_clean['payment_date'] = df_clean['payment_date'].apply(
        lambda x: '9999-12-31' if x == '-' else (x[1:11] if x.startswith('-') else x[:10])
    )
    df_clean['payment_date'] = pd.to_datetime(df_clean['payment_date'], errors='coerce')
    return df_clean



def copy_to_financial_reports(conn, df, table_name='dividend_history'):
    cursor = conn.cursor()
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)
    try:
        cursor.copy_from(buffer, table_name, sep=',')
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        logging.error("Error:", e)
    finally:
        cursor.close()



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
    df = pd.DataFrame()
    for _ in range(5):
        async with ServiceBusClient.from_connection_string(
            conn_str=NAMESPACE_CONNECTION_STR,
            logging_enable=True) as servicebus_client:
            
            async with servicebus_client:
                receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
                async with receiver:
                    
                    received_msgs = await receiver.receive_messages(max_wait_time=30, max_message_count=10)
                    if len(received_msgs) == 0:
                        logging.info("No messages received from the queue. Retrying... {_ + 1}/5")
                        return
                    for msg in received_msgs:
                        logging.info(f"Received message: {str(msg)}")
                        rows = list(page_data(str(msg)))
                        if len(rows) > 0:
                            new_df = pd.DataFrame(data=rows)
                            df = pd.concat([df, new_df], ignore_index=True)
                        else:
                            logging.info(f"No data found for ticker: {str(msg)}")
                            await receiver.complete_message(msg)
                            time.sleep(30)
            if df.shape[0] == 0:
                logging.info("No dividend data received.")
                return        
            df = clean_data(df)
            logging.info(f"Data cleaned. Number of rows: {df.shape[0]}")
            copy_to_financial_reports(conn, df)
            logging.info(f"Data inserted into table: dividend_history")
            return
def main():
    asyncio.run(run_and_receive())
