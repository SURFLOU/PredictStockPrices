import streamlit as st
import pandas as pd
import requests
import altair as alt

API_URL = "http://api:8000"

def fetch_all_tickers():
    response = requests.get(f"{API_URL}/gettickers")
    if response.status_code == 200:
        return response.json()
    return []

def fetch_stock_data(symbol):
    response = requests.get(f"{API_URL}/historical/{symbol}")
    if response.status_code == 200:
        return response.json()["historical_data"]
    return []

def fetch_stock_name(symbol):
    response = requests.get(f"{API_URL}/getstockname/{symbol}")
    if response.status_code == 200:
        return response.json()
    return []

st.title('Stock Price Viewer')

tickers = fetch_all_tickers()

if tickers:
    selected_ticker = st.selectbox('Select a stock ticker', tickers)
    historical_data = fetch_stock_data(selected_ticker)
    if historical_data:
        df = pd.DataFrame(historical_data)
        df['stock_update_date'] = pd.to_datetime(df['stock_update_date'])

        stock_name = fetch_stock_name(selected_ticker[0])
        st.write(f"Displaying data for {selected_ticker}")
        st.write(df[['stock_ticker', 'stock_price', 'stock_update_date']])

        line = alt.Chart(df, title=f'Price of {selected_ticker}').mark_line().encode(
            x='stock_update_date',
            y=alt.Y('stock_price').scale(domain=(df['stock_price'].min(), df['stock_price'].max()))
        )
        st.altair_chart(line)

    else:
        st.error(f"No historical data found for {selected_ticker}")
else:
    st.error("No tickers found. Make sure your database contains stock data.")
