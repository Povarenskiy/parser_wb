import json
import asyncio

from datetime import datetime, timedelta


async def _get_quantity_task(session, article, chrtId):
    """
    Парсер остатка товара на складе 
    """
    basket_api = 'https://ru-basket-api.wildberries.ru/webapi/lk/basket/data?'
    
    # информация об остатке получается post запросом с информацией об артикле и id хранилища
    payload = {
        'basketItems[0][cod1S]': article,
        'basketItems[0][chrtId]': chrtId,
        'basketItems[0][quantity]': 1
    }
    async with session.post(basket_api, data=payload) as basket_response:
        basket_response = json.loads(await basket_response.text())
        stocks = basket_response.get('value').get('data').get('basket').get('basketItems')[0].get('stocks')
        return sum([st.get('qty') for st in stocks])
    

async def get_total_quantity(session, article, data):
    """
    Парсер остатка товара на всех складах 
    """
    # получаем список доступных складов
    chrtIds = [i.get('optionId') for i in data.get('sizes')]
    
    # запуск парсера остатка товара на складах
    tasks = [asyncio.create_task(_get_quantity_task(session, article, chrtId)) for chrtId in chrtIds]
    return sum(await asyncio.gather(*tasks))


async def get_category_path(session, article, data):
    """
    Парсер пути до категории товара
    """
    subject = data.get('subjectId')
    kind = data.get('kindId')
    brand = data.get('brandId')

    category_api = f'https://www.wildberries.ru/webapi/product/{article}/data?subject={subject}&kind={kind}&brand={brand}&targetUrl=PB'

    async with session.get(category_api) as category_response:
        category_json = json.loads(await category_response.text())
        return '/'.join([i['name'] for i in category_json.get('value').get('data').get('sitePath')])


async def get_max_price(session, article):
    """
    Парсер максимальной стоимости за последний месяц
    """
    max_price_per_month = 0 

    last_month = datetime.now() - timedelta(days=31)
    api = f'https://wbx-content-v2.wbstatic.net/price-history/{article}.json'
    
    async with session.get(api) as response:
        response_json = await response.json() 
        for row in response_json:     
            price = row.get('price').get('RUB')
            date = datetime.fromtimestamp(row.get('dt'))
            if date >= last_month:  
                max_price_per_month = max(price, max_price_per_month)
       
        # если за последний месяц нет данных и стоимости, берем последнее значение 
        if not max_price_per_month:
            max_price_per_month = price
        
        return {'max_price_per_month': max_price_per_month}


async def get_sales_count(session, article):
    """
    Парсер количества продаж
    """
    api = f'https://product-order-qnt.wildberries.ru/by-nm/?nm={article}'
    async with session.get(api) as response:
        response_json = await response.json()
        sales_count = response_json[0].get('qnt')
        return {'sales_count': sales_count}


async def get_current_price(session, article):
    """
    Парсер текущей стоимости товара.
    Данный парсер запускает парсеры пути до категории и остатка товара
    """
    price_api = f'https://card.wb.ru/cards/detail?nm={article}'

    async with session.get(price_api) as response:

        response_json = json.loads(await response.text())
        response_json = response_json.get('data').get('products')[0]

        total_quantity = await asyncio.gather(asyncio.create_task(get_total_quantity(session, article, response_json)))
        total_quantity = total_quantity[0]

        # запуск парсера пути до категории товара
        category_path = await asyncio.gather(asyncio.create_task(get_category_path(session, article, response_json)))
        category_path = category_path[0]
            

    current_price =  response_json.get('priceU') or response_json.get('salePriceU')
    return {'current_price': current_price, 'category_path': category_path, 'total_quantity': total_quantity}
    
    