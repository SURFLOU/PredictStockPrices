import requests
import re 
from datetime import datetime 


def import_stock_names_and_tickers():
    url = 'https://www.biznesradar.pl/gielda/akcje_gpw'
    content = requests.get(url).text
    matches = re.findall(r'notowania.*?"change"', content, re.DOTALL)
    for stock in matches:
        if '(' in stock:
            stock_ticker = stock.split('>')[1].split()[0]
        else:
            stock_ticker = stock.split('>')[1].split('<')[0]
        stock_price = stock.split('Close">')[1].split('<')[0]
        stock_price = stock_price.replace(',', '.')
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        print(stock_ticker, stock_price, date)

import_stock_names_and_tickers()