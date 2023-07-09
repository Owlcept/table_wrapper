import aiohttp
import asyncio
import requests
import time
import os , inspect
from sys import _getframe
from dotenv import load_dotenv
from functools import wraps

load_dotenv()


_CO_NESTED = inspect.CO_NESTED
_CO_FROM_COROUTINE = inspect.CO_COROUTINE | inspect.CO_ITERABLE_COROUTINE | inspect.CO_ASYNC_GENERATOR
_isasyncgenfunction = inspect.isasyncgenfunction

def from_coroutine(level=2, _cache={}):
    '''
        Curio

        Copyright (C) 2015-2020
        David Beazley (Dabeaz LLC, https://www.dabeaz.com)
        All rights reserved.
    
    '''
    f_code = _getframe(level).f_code
    if f_code in _cache:
        return _cache[f_code]
    #checking if true aka X > 0 to see if co routine
    if f_code.co_flags & _CO_FROM_COROUTINE:
        _cache[f_code] = True
        return True
    else:
        # Comment:  It's possible that we could end up here if one calls a function
        # from the context of a list comprehension or a generator expression. For
        # example:
        #
        #   async def coro():
        #        ...
        #        a = [ func() for x in s ]
        #        ...
        #
        # Where func() is some function that we've wrapped with one of the decorators
        # below.  If so, the code object is nested and has a name such as <listcomp> or <genexpr>
        if (f_code.co_flags & _CO_NESTED and f_code.co_name[0] == '<'):
            return from_coroutine(level + 2)
        else:
            _cache[f_code] = False
            return False

def awaitable(sfunc):
    '''
        Curio

        Copyright (C) 2015-2020
        David Beazley (Dabeaz LLC, https://www.dabeaz.com)
        All rights reserved.
    
    '''


    def decorate(afunc):
        if inspect.signature(sfunc) != inspect.signature(afunc):
            raise TypeError(f'{sfunc.__name__} and async {afunc.__name__} have different signatures')

        @wraps(afunc)
        def wrapper(*args, **kwargs):
            if from_coroutine():
                return afunc(*args, **kwargs)
            else:
                return sfunc(*args, **kwargs)
        #these wree used for Curio, not needed here unless you need the attrs   
        #wrapper._syncfunc = sfunc
        #wrapper._asyncfunc = afunc
        #wrapper._awaitable = True
        wrapper.__doc__ = sfunc.__doc__ or afunc.__doc__
        return wrapper
    return decorate


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
    

    def rate(self):
        self.usage += 1
        if self.usage >= 30:
            self.usage = 0
            time.sleep(self._ratelimit)
        else:
            pass
    
    @awaitable(rate)
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

    def full_table(self, table:int|str) -> dict:
        #self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        with requests.session() as r:
            data = r.get(url = url, params = self.params)
            data = data.json()
            return data['data']

    @awaitable(full_table)
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

    def single_row(self, table: int|str , id:str):
        self.rate()
        url = f'https://api.tablebackend.com/v1/singleRow/{self.get_table(table)}/{id}'
        with requests.session() as r:
            data = r.get(url = url, params = self.params)
            return data.json()


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

    def add(self, table: int|str, info: list[dict]) -> str:
        self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        with requests.session() as r:
            data = r.post(url = url, params = self.params, json = info)
            data = data.json()
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
            
    def update(self, table: str|int , info: dict) -> bool:
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

        self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        with requests.session() as r:
            data = r.put(url = url, params = self.params, json = info)
            data = data.json()
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

    def delete(self, table: int|str , ids: list[str]):
        self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        with requests.session() as r:
            data = r.delete(url = url, params = self.params, json = ids)
            data = data.json()
            return data

    async def search(self, table: int|str , q:str) -> dict:
        await self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}/search?q={q}'
        async with aiohttp.ClientSession() as r:
            data = await r.get(url = url, params = self.params)
            data = await data.json()
            return data['hits']
        
    def delete(self, table: int|str , ids: list[str]):
        self.rate()
        url = f'https://api.tablebackend.com/v1/rows/{self.get_table(table)}'
        with requests.session() as r:
            data = r.delete(url = url, params = self.params, json = ids)
            data = data.json()
            return data
        
tb = TB(api_key=os.getenv("API"), db = [os.getenv("DB")])
print(tb.full_table(0))

async def main():
    x = await tb.full_table(0)
    print(x)

asyncio.run(main())