from datetime import datetime
from airflow import DAG
from airflow.operators.python_operator import PythonOperator

def insert_stocknames_table():
    return 'Hello world from first Airflow DAG!'

dag = DAG('insert_stocknames_table', description='Insert stock name and ticker',
          schedule_interval=None,
          start_date=datetime(2017, 3, 20), catchup=False)

insert_stocknames = PythonOperator(task_id='insert_stocknames_table', python_callable=insert_stocknames_table, dag=dag)

insert_stocknames