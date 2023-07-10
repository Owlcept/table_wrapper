# Welcome to TB
#### This is an async wrapper for the api of [tablebackend](https://tablebackend.com/) , a simple backend service

---
### How to *use*
So to start you will need your api_key (if your table is secured)

With your key you will now create your instance as such
```python
from tb import TB #This will import the right class
tb = TB(api_key=key, db=list[db,...])
#all methods use this structure || tb.full_table(table)
```
This will now allow you access to the all the databases you have passed into the class.

The basic functions are as follows
All functions may be used in async or sync
*side note: all tables can be given by index in the list or by the str of the table*
- .full_table(table: int|str)
	- returns all data in table

	
- .single_row(table: int|str, id: str)
	- returns a single row by id

	
- .add(table:int|str, info: list[dict])
	- adds a new row(s) to given table
	- must fulfill all your table requirements

	
- .update(table: int|str, info: dict)
	- updates a row in the given table
	- must use _id though
	- returns if successful or not

	
- .delete(table: int|str, ids: list[str])
	- deletes the row id(s) given
	- returns if successful or not
- .search(table: int|str, q: str)
	- returns all hits on queried data
	- make sure you index all data you want to be able to search

- .get_ids(table: int|str, q: str)
	- does the same thing as search but returns all the ids of items you want to use for deletion or updating
	- this is SYNC only **do not await**
