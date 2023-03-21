import aiohttp
import asyncio

from database import *
from parsers import *





async def get_items_data(session, article, db):
    """
    Запуск парсеров по артиклю товара
    """
    tasks = [
        asyncio.create_task(get_max_price(session, article)),
        asyncio.create_task(get_sales_count(session, article)),
        asyncio.create_task(get_current_price(session, article)),
    ]
    responses = await asyncio.gather(*tasks)

    # запись в базу данных
    data = {'article': article}
    for response in responses:
        data.update(response)
    await db.write(**data)
  

async def main():    
    # Получаем список артиклей товаров 
    article_list = [int(article) for article in open('article_list.txt')]

    # создаем и подключаемся в базеданных
    db = Database('sqlite.db', 'products')
    await db.create()

    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(get_items_data(session, article, db))
            for article in article_list
        ]
        await asyncio.gather(*tasks)
    
    await db.read()
    await db.close()    
    


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
     