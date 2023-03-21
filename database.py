import aiosqlite

class Database:
    
    def __init__(self, name, table):
        self.name = name
        self.table = table 


    async def create(self):
        self.db = await aiosqlite.connect(self.name) 
        self.cursor = await self.db.cursor() 
        
        await self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {self.table} (
                article integer,
                current_price integer,
                category_path varchar(255),
                sales_count integer,
                max_price_per_month integer,
                total_quantity integer)
            """)


    async def write(self, article, current_price, category_path, sales_count, max_price_per_month, total_quantity):    
        sql = f"""
        INSERT INTO products (article, current_price, category_path, sales_count, max_price_per_month, total_quantity)
        VALUES (?,?,?,?,?,?)
        """
        await self.cursor.execute(sql, [article, current_price, category_path, sales_count, max_price_per_month, total_quantity])
        await self.db.commit()


    async def read(self):
        await self.cursor.execute(f"""SELECT * FROM products""")
        results = await self.cursor.fetchall() 
        for row in results:
            print(row)


    async def close(self):
        await self.cursor.close()
        await self.db.close()



































