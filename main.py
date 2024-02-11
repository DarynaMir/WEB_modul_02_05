import aiohttp
import asyncio
import platform
import sys
import json
from datetime import datetime, timedelta


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


async def main(index_day):
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
                        'saleRate': currency_data.get('saleRate'),
                        'purchaseRate': currency_data.get('purchaseRate')
                    } for currency_data in response['exchangeRate']
                    if currency_data['currency'] in ['EUR', 'USD']
                }
            }
            exchange_rates.append(filtered_data)
        except HttpError as err:
            print(err)

    return exchange_rates


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    index_day = int(sys.argv[1])
    try:
        exchange_rates = asyncio.run(main(index_day))
        print(json.dumps(exchange_rates, indent=2))
    except ValueError as err:
        print(err)
