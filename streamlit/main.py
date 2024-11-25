import streamlit as st
import altair as alt 
import psycopg2
import pandas as pd 
import matplotlib.pyplot as plt

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

df = pd.read_sql("SELECT * FROM StockDailyPrices", conn)


df['stock_update_date'] = pd.to_datetime(df['stock_update_date'])


st.title('Stock Price Viewer')


tickers = df['stock_ticker'].unique()
selected_ticker = st.selectbox('Select a stock ticker', tickers)


filtered_df = df[df['stock_ticker'] == selected_ticker]


st.write(f"Displaying data for {selected_ticker}")
st.write(filtered_df[['stock_ticker', 'stock_price', 'stock_update_date']])

line = alt.Chart(filtered_df, title=f'Price of {selected_ticker}').mark_line().encode(
    x = 'stock_update_date',
    y = alt.Y('stock_price').scale(domain=(filtered_df['stock_price'].min(), filtered_df['stock_price'].max()))
)

st.altair_chart(line)
