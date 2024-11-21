import streamlit as st
import psycopg2

def connect_to_db():
    conn = psycopg2.connect(
        dbname="airflow",
        user="airflow",
        password="airflow",
        host="postgres"
)
    cursor = conn.cursor()
    return cursor, conn
 

db_conn = connect_to_db()
cursor = db_conn[0]
conn = db_conn[1]

if st.button("FETCH DATA"):
    cursor.execute("""
    DROP TABLE IF EXISTS StockNames;               
    CREATE TABLE StockNames(id SERIAL PRIMARY KEY,
                   stock_ticker VARCHAR(255),
                   stock_name VARCHAR(255)
                   );
    INSERT INTO StockNames (stock_ticker, stock_name) VALUES ('DVL', 'DEVELIA');
    SELECT * FROM StockNames;            
                   """)
    conn.commit()
    rows = cursor.fetchall()
    for row in rows:
        st.write(row)

print("Connected")