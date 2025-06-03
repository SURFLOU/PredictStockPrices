# Financial Reports Scraper

> **Warning:** This tool is intended for educational and personal use only. Respect the website’s terms of service and robots.txt.  

Te dane to nie jest porada inwestycyja 

TBD - wrzucic do AZURE FUNCTION + SPAROWAC Z AZURE QUEUE

---

## 📄 Description

This Python script scrapes financial report data from BiznesRadar’s Profit and Loss Reports page for a given stock ticker. It retrieves key metrics (Sales Revenue, Gross Profit, EBIT, Operating Profit, Net Profit, EBITDA) across multiple years, cleans and formats the data into a Pandas DataFrame, then inserts it into a PostgreSQL table named `financial_reports`.

- **Source URL template:**  
  `https://www.biznesradar.pl/raporty-finansowe-rachunek-zyskow-i-strat/{ticker}`

- **Key Features:**  
  1. Send an HTTP GET request with a browser-like User-Agent  
  2. Parse the HTML table using BeautifulSoup  
  3. Map Polish column headers to English field names  
  4. Clean numeric values (remove spaces, convert to `int`)  
  5. Insert the DataFrame into a PostgreSQL/Citus table via `psycopg2.copy_from()`  

---

## 🔧 Prerequisites

- Python 3.7+  
- PostgreSQL database (e.g., Azure Cosmos DB for PostgreSQL / Citus)  
- Network access to the PostgreSQL server (port 5432 open, SSL if required)
- Azure od kolegi
- 

---

## 📦 Installation

1. **Clone or download this repository**  
   
   git clone -b dev https://github.com/SURFLOU/PredictStockPrices.git
   cd function\scrap_financial_reports

2. **Jak dalej nie wiesz co z tym zrobic to lepiej to zostaw**

## 🗄️ Database Schema
    CREATE TABLE IF NOT EXISTS financial_reports (
    ticker         TEXT,
    year           TEXT,
    sales_revenue  INT,
    gross_profit   INT,
    EBIT           INT,
    operating_profit INT,
    net_profit     INT,
    EBITDA         INT
);
-- (If using Citus for distribution:)
SELECT create_distributed_table('financial_reports', 'ticker');

**Column Descriptions:**

    ticker – Stock ticker (e.g., "PKN")
    year – Four-digit year (e.g., "2023")
    sales_revenue – Przychody ze sprzedaży (Sales Revenue)
    gross_profit – Zysk ze sprzedaży (Gross Profit)
    EBIT – Zysk operacyjny (EBIT)
    operating_profit – Zysk z działalności gospodarczej (Operating Profit)
    net_profit – Zysk netto (Net Profit)
    EBITDA – EBITDA

## 📄 License
This project is provided under the DXC kradziony abonament na Azure

## 😜 Additional info 
---
  _______________
 /               \
|   TRZASKOWSKI   |
|       TO        |
|      PAŁA       |
 \_______________/
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\
                ||----w |
                ||     ||

---
## 🤝 Acknowledgments
---
BiznesRadar.pl – Source of financial data
Piter x2, Kuba, Mati - Hardworkers + prezes
Requests & BeautifulSoup – For HTML parsing
Pandas – For DataFrame manipulation
psycopg2 – For PostgreSQL connectivity
You – For reading this README!
---