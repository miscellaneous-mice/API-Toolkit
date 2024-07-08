from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import Pool
from functools import partial
from itertools import repeat
import time


def sp_l(list, c_size):
    for i in range(0, len(list), c_size):
        yield list[i:i+c_size]

def show_exp(value):
    emojis = {0: ':)', 1: ':_(', 2: '(-_-)'}
    rem = value % 3
    print(emojis[rem])

def expressions(data):
    with ThreadPoolExecutor(5) as executor:
        executor.map(show_exp, data)
    print("---------Next Set of Emotions----------")
    time.sleep(1)

if __name__ == '__main__':
    emojis = {0: ':)', 1: ':_(', 2: '(-_-)'}
    data = list(range(100))
    with ProcessPoolExecutor(5) as executor:
        worker = partial(expressions, emojis)
        executor.map(expressions, sp_l(data, 5))
    # with Pool(5) as p:
    #     p.map(expressions, sp_l(data, 10))
