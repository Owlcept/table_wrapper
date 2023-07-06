import aiohttp
import asyncio


class TB:

    def __init__(self, api_key:str = None, db:list[str] = None):
        self._db = db
        self._ratelimit = 2
        self._usage = 0
        self._params = {'api_key': api_key}

    @property
    def db(self):
        return self._db
    
    @property
    def params(self):
        return self._params
    
    @property
    def usage(self):
        return self._usage
    
    @usage.setter
    def usage(self, value):
        self._usage = value

    '''
        These functions are for utility purposes
    '''

    def get_table(self, table: int|str):
        return self._db[self._db.index(table)] if type(table) != int else self._db[table]
    
    async def get_ids(self, table: int|str, q: str) -> list[str]:
        await self.rate()
        ids = []
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}/search?q={q}'
        async with aiohttp.ClientSession() as r:
            data = await r.get(url = url, params = self.params)
            data = await data.json()
            for _ in data['hits']:
                ids.append(_['_id'])
            return ids
    
    async def rate(self):
        self.usage += 1
        if self.usage >= 30:
            self.usage = 0
            await asyncio.sleep(self._ratelimit)
        else:
            pass
    
    '''
        These are main functions
    '''

    async def full_table(self, table:int|str) -> dict:
        await self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        async with aiohttp.ClientSession() as r:
            data = await r.get(url = url, params = self.params)
            data = await data.json()
            return data['data']

    async def single_row(self, table: int|str , id:str):
        await self.rate()
        url = f'https://api.tablebackend.com/v1/singleRow/{self.get_table(table)}/{id}'
        async with aiohttp.ClientSession() as r:
            data = await r.get(url = url, params = self.params)
            return await data.json()

    async def add(self, table: int|str, info: list[dict]) -> str:
        await self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        async with aiohttp.ClientSession() as r:
            data = await r.post(url = url, params = self.params, json = info)
            data = await data.json()
            if 'acknowledged' in data.keys():
                return data['acknowledged']
            if 'error' in data.keys():
                print(f'Error: {data["code"]} - {data["info"]} \nTry again')



    async def update(self, table: str|int , info: dict) -> bool:
        """
        This function updates a row in the databse

        ---
        Params:
        -------
        - table: int | str
            - the table to use or find for use
        - info: dict
            - `MUST` start with {'_id': str} to decide which row to update
        """

        await self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        async with aiohttp.ClientSession() as r:
            data = await r.put(url = url, params = self.params, json = info)
            data = await data.json()
            if 'error' in data.keys():
                print(f'Error: {data["code"]} - {data["info"]} \nTry again')
            else:
                return True

    async def delete(self, table: int|str , ids: list[str]):
        await self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        async with aiohttp.ClientSession() as r:
            data = await r.delete(url = url, params = self.params, json = ids)
            data = await data.json()
            return data

    async def search(self, table: int|str , q:str) -> dict:
        await self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}/search?q={q}'
        async with aiohttp.ClientSession() as r:
            data = await r.get(url = url, params = self.params)
            data = await data.json()
            return data['hits']