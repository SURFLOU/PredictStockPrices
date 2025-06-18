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

load_dotenv()
NAMESPACE_CONNECTION_STR = os.getenv('queue_connstring')
QUEUE_NAME = "dividend_queue"
CONN_STRING = os.getenv("postgres-connstring")

#  
#db connection
conn = psycopg2.connect(CONN_STRING)

cursor = conn.cursor()

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
            print(data)
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



def copy_to_financial_reports(conn, df):
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)
    cursor = conn.cursor()
    try:
        cursor.copy_from(buffer, "dividend_history", sep=',')
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print("Error:", e)
    finally:
        cursor.close()



async def run_and_receive():
    df = pd.DataFrame()
    async with ServiceBusClient.from_connection_string(
        conn_str=NAMESPACE_CONNECTION_STR,
        logging_enable=True) as servicebus_client:
        
        async with servicebus_client:
            receiver = servicebus_client.get_queue_receiver(queue_name=QUEUE_NAME)
            async with receiver:
                
                received_msgs = await receiver.receive_messages(max_wait_time=5, max_message_count=450)
                for msg in received_msgs[:30]:
                    time.sleep(30)
                    try:
                        body = b"".join(msg.body).decode("utf-8")
                    except Exception as e:
                        print(f"Failed to decode message: {e}")
                        await receiver.abandon_message(msg)
                        continue
                    print("Received:", body)

                    try:
                        rows = page_data(body)
                        new_df = [x for x in rows]
                        new_df = pd.DataFrame(data=new_df)
                        df = pd.concat([df, new_df], ignore_index=True)
                        
                        await receiver.complete_message(msg)
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        await receiver.abandon_message(msg)
                
        df = clean_data(df)
        
        copy_to_financial_reports(conn, df)

def main():
    asyncio.run(run_and_receive())