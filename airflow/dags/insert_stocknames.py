from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import requests
import re 
import psycopg2 

def import_stock_names_and_tickers(**kwargs):
    url = 'https://www.biznesradar.pl/gielda/akcje_gpw'
    content = requests.get(url).text
    matches = re.findall(r'\/notowania\/.*<\/a>', content)
    stocks = []
    for match in matches:
        stock_name = match.split('title="')[1].split('"')[0]
        if '(' in match:
            ticker = match.split('>')[1].split()[0]
        else:
            ticker = match.split('>')[1].split('<')[0]
        stocks.append([ticker, stock_name])
    return stocks

def insert_to_db(**kwargs):
    ti = kwargs['ti']
    stocks = ti.xcom_pull(task_ids='import_stocknames')
    conn = psycopg2.connect(
        dbname="airflow",
        user="airflow",
        password="airflow",
        host="postgres"
    )
    cursor = conn.cursor()
    cursor.execute("""
    DROP TABLE IF EXISTS StockNames;               
    CREATE TABLE StockNames(id SERIAL PRIMARY KEY,
                   stock_ticker VARCHAR(255),
                   stock_name VARCHAR(255)
                   );         
                   """)
    conn.commit()
    for stock in stocks:
        query = f"INSERT INTO StockNames (stock_ticker, stock_name) VALUES ('{stock[0]}', '{stock[1]}');"
        cursor.execute(query)
        conn.commit()

dag = DAG('insert_stocknames_table', description='Insert stock name and ticker',
          schedule_interval=None,
          start_date=datetime(2017, 3, 20), catchup=False)

import_stocknames = PythonOperator(task_id='import_stocknames', python_callable=import_stock_names_and_tickers, provide_context=True, dag=dag)
insert_to_db = PythonOperator(task_id='insert_to_db', python_callable=insert_to_db, provide_context=True, dag=dag)


import_stocknames >> insert_to_db