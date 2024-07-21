from functools import wraps
import os
import sys
import json
import logging
import pandas as pd
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
    log_folder = os.getcwd() + '/logs/{logger_name}\\'
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
            key = ''.join(list(map(str, args))) + json.dumps(kwargs)
            # if not key in cache.keys():
            if not isinstance(cache.get(key), pd.DataFrame):
                tem = await func(*args, **kwargs)
                cache.set(key, tem, ttl=20, parquet=True)
            else:
                tem = cache.get(key)
            return tem
        return _wrapper
    return cache_func