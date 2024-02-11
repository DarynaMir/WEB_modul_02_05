import aiohttp
import asyncio
import platform
import sys
import json
from datetime import datetime, timedelta
import websockets

class HttpError(Exception):
    pass

async def request(url: str):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result
                else:
                    raise HttpError(f'Error status: {resp.status} for {url}')
        except aiohttp.ClientConnectorError as err:
            raise HttpError(f'Connection error: {url}', str(err))
        except aiohttp.ClientTimeout as err:
            raise HttpError(f'Timeout error: {url}', str(err))
        except aiohttp.InvalidURL as err:
            raise HttpError(f'Invalid URL error: {url}', str(err))
        except aiohttp.ClientResponseError as err:
            raise HttpError(f'Client response error: {url}', str(err))
        except Exception as err:
            raise HttpError(f'An unexpected error occurred: {url}', str(err))

async def exchange_command():
    url = 'https://api.privatbank.ua/p24api/pubinfo?json&exchange&coursid=5'
    try:
        response = await request(url)
        exchange_data = {}
        for currency in response:
            if currency['ccy'] in ['EUR', 'USD']:
                exchange_data[currency['ccy']] = {
                    'Buy': currency['buy'],
                    'Sell': currency['sale']
                }
        return exchange_data
    except HttpError as err:
        return {'error': str(err)}

async def main(index_day, currencies):
    max_days = 10
    if index_day > max_days:
        raise ValueError("Cannot fetch exchange rates for more than the last 10 days.")

    exchange_rates = []
    for i in range(index_day, 0, -1):
        d = datetime.now() - timedelta(days=i)
        shift = d.strftime('%d.%m.%Y')
        url = f'https://api.privatbank.ua/p24api/exchange_rates?date={shift}'

        try:
            response = await request(url)
            filtered_data = {
                shift: {
                    currency_data['currency']: {
                        'sale': currency_data.get('saleRate'),
                        'purchase': currency_data.get('purchaseRate')
                    } for currency_data in response['exchangeRate']
                    if currency_data['currency'] in currencies
                }
            }
            exchange_rates.append(filtered_data)
        except HttpError as err:
            print(err)

    return exchange_rates

async def handle_command(websocket, command):
    if command == 'exchange':
        exchange_data = await exchange_command()
        await websocket.send(json.dumps({'type': 'exchange_data', 'content': exchange_data}))
    else:
        await websocket.send(json.dumps({'type': 'error', 'content': f'Unknown command: {command}'}))

async def handle_connection(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        if 'type' in data and data['type'] == 'command':
            await handle_command(websocket, data['content'])

if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    start_server = websockets.serve(handle_connection, "localhost", 8765)

    index_day = int(sys.argv[1])
    selected_currencies = sys.argv[2:]

    try:
        exchange_rates = asyncio.run(main(index_day, selected_currencies))
        print(json.dumps(exchange_rates, indent=2))
    except ValueError as err:
        print(err)

