import requests
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
from io import StringIO
import os

def scrap_financial_reports(ticker: str) -> pd.DataFrame:
    # adres
    url = f"https://www.biznesradar.pl/raporty-finansowe-rachunek-zyskow-i-strat/{ticker}"

    # jestem przegladarką
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    # GET request
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # nazwy kolumn pl: eng
    TITLES = {
        "Przychody ze sprzedaży": "sales_revenue",
        "Zysk ze sprzedaży": "gross_profit",
        "Zysk operacyjny (EBIT)": "EBIT",
        "Zysk z działalności gospodarczej": "operating_profit",
        "Zysk netto": "net_profit",
        "EBITDA": "EBITDA"
    }

    # start scrapping
    table = soup.find("table", class_="report-table")
    if not table:
        raise ValueError("Financial report table not found on page.")

    # Extract and clean year headers
    header_cells = table.find("tr").find_all("th")[1:-1]
    years = [cell.get_text(strip=True).split("(")[0] for cell in header_cells]

    # Initialize dictionary for data
    data_dict = {"year": years}

    # Extract rows matching specified titles
    for row in table.find_all("tr")[1:]:
        label_cell = row.find("td", class_="f")
        if not label_cell:
            continue

        title_pl = label_cell.get_text(strip=True)
        if title_pl in TITLES:
            title_en = TITLES[title_pl]
            values = []
            for cell in row.find_all("td", class_="h"):
                # Prefer <span class="pv">, fallback to <span class="premium-value">
                span = cell.find("span", class_="pv")
                if span:
                    val = span.get_text(strip=True)
                else:
                    premium_span = cell.find("span", class_="premium-value")
                    if premium_span:
                        val = premium_span.get_text(strip=True)
                    else:
                        val = ""
                values.append(val)
            data_dict[title_en] = values

    # print(data_dict)

    # Convert to DataFrame
    df = pd.DataFrame(data_dict)

    # Reorder columns (optional)
    df = df[["year"] + list(TITLES.values())]

    # print(df.head())

    # czyszczenie
    # Wywalenie estymatow
    df = df[df['year'].astype(str).str.match(r'^\d{4}$')]

    # print(df.head())

    # dodanie tickera
    df.insert(0, 'ticker', ticker)

    # formatowanie - ticker, year -> str
    df['ticker'] = df['ticker'].astype(str)
    df['year'] = df['year'].astype(str)

    # formatowanie - usuniecie spacji, type to int
    cols_to_convert = df.columns[2:8]
    for col in cols_to_convert:
        df[col] = df[col].str.replace(' ', '', regex=False)  # remove spaces
        df[col] = pd.to_numeric(df[col], errors='coerce')  # convert to numbers

    return df

def copy_to_financial_reports(conn, df, ticker):
    buffer = StringIO()
    df.to_csv(buffer, index=False, header=False)
    buffer.seek(0)
    cursor = conn.cursor()
    try:
        cursor.copy_from(buffer, "financial_reports", sep=',')
        conn.commit()
        print(f"{ticker} data inserted into financial_reports.")
    except Exception as e:
        conn.rollback()
        print("Error:", e)
    finally:
        cursor.close()


# Connect to the Azure Cosmos DB for PostgreSQL instance
conn = psycopg2.connect(
    host=os.getenv('HOST'),
    port=os.getenv('PORT'),
    dbname=os.getenv('DATABASE'),
    user=os.getenv('USER'),
    password=os.getenv('PASSWORD'),
    sslmode="require"  # Cosmos DB requires SSL
)

print(conn)

# df = scrap_financial_reports("KGHM")
# print(df.head())
# print(df.info())
#

# 1. add kolejka z azura
# 2. wyczyscic tabele po testach - done 

for tic in ['CCC']:
    df = scrap_financial_reports(tic)
    print(df.head())
    copy_to_financial_reports(conn, df, tic)