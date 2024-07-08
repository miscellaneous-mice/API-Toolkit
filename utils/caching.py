import os
import json
import time
import sys
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import pyarrow as pa
import concurrent.futures
from typing import Optional, Any, Union
from diskcache import FanoutCache
from functools import wraps

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='list')
        return super().default(obj)

class CacheOps:
    DEFAULT_NAME = "cache_db"
    DEFAULT_TTL = 600
    FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(lineno)d — %(funcName)s — %(message)s")
    def __init__(self, cache_dir=os.path.join(os.getcwd(), 'cache_dir'),
                eviction_policy='lrs', cache_size=12):
        self.logger = self.init_logger("Cache")
        self.eviction_mapping = {
            'lrs' : 'least-recently-stored',
            'lru' : 'least-recently-used',
            'lfu' : 'least-frequently-used'
        }
        self._validate_cache(cache_dir, cache_size, eviction_policy)
        if not self.cache_exists():
            self.cache = FanoutCache(self.cache_dir).cache(
                name=self.DEFAULT_NAME,
                size=self.cache_size * 1024 * 1024 * 1024,
                eviction_policy=self.eviction_policy
            )
        else:
            self.logger.info(f"Using existing cache at {self.cache_dir}")
    
    def _validate_cache(self, cache_dir, cache_size, eviction_policy):
        self.cache_dir = os.path.abspath(cache_dir)
        self.cache_size = int(cache_size)
        self.eviction_policy = self.eviction_mapping[eviction_policy]
        self.logger.info(f"Setting the cache at {self.cache_dir}.")
        

    def cache_exists(self):
        self.cache = FanoutCache(self.cache_dir).cache(name=self.DEFAULT_NAME)
        return len(self.keys()) > 0

    def get(self, key: str,
            parquet: bool = False) -> Optional[Any]:
        start_time = time.time()
        value = self.cache.get(key, default=None)
        get_time = time.time() - start_time
        if value is not None:
            expire_time, size, data = value
            if isinstance(data, bytes):
                parquet = True
            if expire_time is None or expire_time > time.time():
                self.logger.info(f"Size of {key} is {size} bytes")
                if parquet:
                    self.logger.info(f"Retrieved key : {key}. Get time = {get_time}")
                    return self.from_parquet(data)
                else:
                    self.logger.info(f"Retrieved key : {key}. Get time = {get_time}")
                    return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str,
            value: Union[dict, list, pd.DataFrame, bytes, str], 
            parquet: bool = False, ttl: Optional[int] = DEFAULT_TTL):
        if parquet:
            value = self.to_parquet(pd.DataFrame([{'data': json.dumps(value, cls=NumpyEncoder)}]))
        expire_time = None
        if ttl is not None:
            expire_time = time.time() + ttl
        else:
            self.logger.info("TTL is None. key will not expire")
        size = sys.getsizeof(value)
        self.cache.set(key, (expire_time, size, value), expire=expire_time)
        self.logger.info(f"Set key: {key}")
    
    def to_parquet(self, df: pd.DataFrame):
        parquet_data = df.to_parquet()
        return parquet_data
    
    def from_parquet(self, cache_data: bytes):
        buffer_reader = pa.BufferReader(cache_data)
        parquet_table = pa.parquet.read_table(buffer_reader)
        data = parquet_table.to_pandas()
        return json.loads(data['data'].iloc[0].replace('NaN', 'null'))

    def get_size(self, key):
        _, size, _ = self.cache.get(key)
        return size
    
    def delete_expired_key(self, key):
        value = self.cache.get(key, default=None)
        if value is not None:
            expire_time, data = value
            if expire_time < time.time():
                del self.cache[key]

    def delete_expired_keys(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.delete_expired_key, self.cache.iterkeys())

    def keys(self):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.map(self.delete_expired_key, self.cache.iterkeys())
        return list(self.cache.iterkeys())
    
    def get_console_handler(self):
        '''Get formatter'''
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.FORMATTER)
        return console_handler

    def init_logger(self, logger_name):
        '''
        This functions is used for logging.

        params:
            logger_name (str): file name

        returns:
            logger: to log the required outputs
        '''
        date = str(datetime.now().date())
        log_folder = f'/Users/prateek/My Space/Projects/Performance/logs/cache_logs/{logger_name}\\'
        file_name = f"{log_folder}\\{logger_name}_{date}.log"

        if not (os.path.isdir(log_folder)):
            os.makedirs(log_folder, exist_ok=True)
        logger = logging.getLogger(logger_name)
        # better to have too much log than not enough
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self.get_console_handler())
        # with this pattern, it's rarely necessary to propagate the error up to parent
        logger.propagate = False
        return logger
                
if __name__ == '__main__':
    m1 = [{'a': [1, 2, 3], 'b': [4, 5, 6], 'c': [7, 8, 9]}, ['xyz', 'abc', 'lmao'], 'Python is cool']
    # m1 = {'one': [-1, np.nan, 2.5],
    #                'two': ['foo', 'bar', 'baz'],
    #                'three': [True, False, True]}
    m2 = {'ds1' : {'a': [1, 2, 3], 'b': [4, 5, 6], 'c': [7, 8, 9], 'd': ['xyz', 'abc', 'lmao'], 'e': 'NFS'},
        'ds2' : [[{'a': [1, 2, 3], 'b': [4, np.nan, 6], 'c': [7, 8, 9]}, ['xyz', 'abc', 'lmao']], ['Python is cool',
                {1 : ['a', 'b', 'c'], 2: {'a': [1, 2, 3], 'b' : [4, 5, 6]}, 3: 'Hola'}]],
        'ds3': 'Hello, sayonara'}
    m3 = {'np': np.random.randn(1000, 1000), 
        'pd' : pd.DataFrame({'a' : np.arange(0, 1000), 
                            'b' : np.arange(0, 1000),
                            'c' : np.random.randn(1000)})}  
    

    cache = CacheOps(cache_dir=os.path.join(os.getcwd(), 'cache_dir'))
    cache.set('m1', m1, ttl=10, parquet=True)
    cache.set('m2', m2, ttl=10, parquet=True)
    cache.set('mp', m3, ttl=10, parquet=True)
    cache.set('mnp', m3, ttl=10)

    st = time.time()
    mp = cache.get('mp')
    et1 = time.time() - st

    st = time.time()
    mnp = cache.get('mnp')
    et2 = time.time() - st
    breakpoint()
    

