from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import requests
import re 
import psycopg2 

def import_stock_prices(**kwargs):
    url = 'https://www.biznesradar.pl/gielda/akcje_gpw'
    content = requests.get(url).text
    matches = re.findall(r'notowania.*?"change"', content, re.DOTALL)
    stocks = []
    for stock in matches:
        if '(' in stock:
            stock_ticker = stock.split('>')[1].split()[0]
        else:
            stock_ticker = stock.split('>')[1].split('<')[0]
        stock_price = stock.split('Close">')[1].split('<')[0]
        stock_price = stock_price.replace(',', '.')
        stock_price = stock_price.replace(' ', '')
        if len(stock_ticker) > 4:
            continue
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        stocks.append([stock_ticker, stock_price, date])
    return stocks

def insert_to_db(**kwargs):
    ti = kwargs['ti']
    stocks = ti.xcom_pull(task_ids='import_stockprices')
    conn = psycopg2.connect(
        dbname="airflow",
        user="airflow",
        password="airflow",
        host="postgres"
    )
    cursor = conn.cursor()
    cursor.execute("""             
    CREATE TABLE IF NOT EXISTS StockDailyPrices(id SERIAL PRIMARY KEY,
                   stock_ticker VARCHAR(255),
                   stock_price NUMERIC,
                   stock_update_date TIMESTAMP
                   );         
                   """)
    conn.commit()
    for stock in stocks:
        query = f"INSERT INTO StockDailyPrices (stock_ticker, stock_price, stock_update_date) VALUES ('{stock[0]}', '{stock[1]}', '{stock[2]}');"
        cursor.execute(query)
        conn.commit()

dag = DAG('insert_stockprices_daily_table', description='Insert stock daily price',
          schedule_interval="0,15,30,45 9-16 * * 1,2,3,4,5",
          start_date=datetime(2017, 3, 20), catchup=False)

import_stockprices = PythonOperator(task_id='import_stockprices', python_callable=import_stock_prices, provide_context=True, dag=dag)
insert_to_db = PythonOperator(task_id='insert_to_db', python_callable=insert_to_db, provide_context=True, dag=dag)


import_stockprices >> insert_to_db