import inspect
from sys import _getframe
from functools import wraps



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