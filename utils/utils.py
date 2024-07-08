from functools import wraps
import os
import sys
import logging
from datetime import datetime

FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s — %(lineno)d — %(funcName)s — %(message)s")

def get_console_handler():
    '''Get formatter'''
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_logger(logger_name):
    '''
    This functions is used for logging.

    params:
        logger_name (str): file name

    returns:
        logger: to log the required outputs
    '''
    date = str(datetime.now().date())
    log_folder = f'/Users/prateek/My Space/Projects/Performance/logs/{logger_name}\\'
    file_name = f"{log_folder}\\{logger_name}_{date}.log"

    if not (os.path.isdir(log_folder)):
        os.makedirs(log_folder, exist_ok=True)
    logger = logging.getLogger(logger_name)
    # better to have too much log than not enough
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_console_handler())
    # with this pattern, it's rarely necessary to propagate the error up to parent
    logger.propagate = False
    return logger

def sp_l(list, c_size):
    for i in range(0, len(list), c_size):
        yield list[i:i+c_size]

def cacheWrapper(cache):
    def cache_func(func):
        @wraps(func)
        async def _wrapper(*args, **kwargs):
            if not 'key' in kwargs:
                tem = await func(*args, **kwargs)
                return tem
            key = kwargs['key']
            if not key in cache.keys():
                tem = await func(*args, **kwargs)
                cache.set(key, tem, ttl=1200, parquet=True)
            else:
                tem = cache.get(key)
            return tem
        return _wrapper
    return cache_func