from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from pyspark.sql import SparkSession
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2024, 11, 22),
}

dag = DAG(
    'test_pyspark',
    default_args=default_args,
    description='A simple PySpark DAG',
    schedule_interval='@daily', 
    catchup=False,
)

def run_pyspark_job():
    spark = SparkSession.builder \
        .appName("Simple PySpark Job") \
        .getOrCreate()
    
    data = [("Alice", 1), ("Bob", 2), ("Charlie", 3)]
    columns = ["name", "value"]
    df = spark.createDataFrame(data, columns)
    
    df.show()

    df_transformed = df.withColumn("value_plus_10", df["value"] + 10)
    
    df_transformed.show()

    spark.stop()

pyspark_task = PythonOperator(
    task_id='run_pyspark_task',
    python_callable=run_pyspark_job,
    dag=dag,
)


