import logging
import asyncio
import json
import os
import re
from azure.eventhub import EventData
from azure.eventhub.aio import EventHubProducerClient
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import logging 


logging.basicConfig(level=logging.INFO)


EVENT_HUB_CONNECTION_STR = os.getenv("EVENT_HUB_CONNECTION_STR")
EVENT_HUB_NAME = os.getenv("EVENT_HUB_NAME")

def get_live_prices():
    url = 'https://www.biznesradar.pl/gielda/akcje_gpw'
    page_content = requests.get(url).text
    pattern = re.compile(
        r'<td><a href="/notowania/(?P<ticker>[^"]+)"[^>]*>(?P<ticker_name>[^<]+)</a></td>\s*'
        r'<td[^>]*>.*?</td>\s*'
        r'<td[^>]*><span[^>]*>(?P<price>[\d,]+)</span></td>\s*'
        r'<td[^>]*>.*?</td>\s*',
        re.DOTALL
    )

    current_time = datetime.now(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M:%S")
    for match in pattern.finditer(page_content):
        ticker_name = match.group('ticker_name').strip()
        ticker = ticker_name.split(' (')[0].strip()
        price = match.group('price').replace(',', '.')
        yield {'ticker': ticker, 'price': price, 'time': current_time}


async def main_loop():
    try:
        producer = EventHubProducerClient.from_connection_string(
            conn_str=EVENT_HUB_CONNECTION_STR,
            eventhub_name=EVENT_HUB_NAME
        )

        async with producer:
            batch = await producer.create_batch()
            for event in get_live_prices():
                batch.add(EventData(json.dumps(event)))
                logging.info(f"Sending event: {event}")
            await producer.send_batch(batch)

    except Exception as e:
        logging.exception("Unhandled error while sending events to Event Hub")

def main():
    asyncio.run(main_loop())