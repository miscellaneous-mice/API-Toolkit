import os
import sys
from functools import cache
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import scipy
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import repeat
from utils import cacheWrapper

matplotlib.use('Agg')
sns.set_style('darkgrid')


class Calculations:
    @cache
    def factorial(self, n):
        result = 1
        for i in range(1, n+1):
            result *= i
        return result
    
    async def interpolate(self, process_type):
        cycles = 25
        resolution = 200
        length = np.pi * 2 * cycles
        x = np.arange(0, length, length / resolution)
        smooth_x = np.linspace(0, length, 1500)
        y = np.arange(0, length, length / resolution)
        smooth_y = smooth_x.copy()
        z_sin = np.sin(x**2 + y**2)
        z_cos = np.cos(x**2 + y**2)
        result = []
        if process_type == 'multithreading':
            with ThreadPoolExecutor(2) as executor:
                res = executor.map(self.rbf, repeat(x), repeat(y),
                                repeat(smooth_x), repeat(smooth_y), [z_sin, z_cos])
            result = list(res)
            inter_sin = result[0]
            inter_cos = result[1]
        elif process_type == 'multiprocessing':
            with ProcessPoolExecutor(2) as executor:
                res = executor.map(self.rbf, repeat(x), repeat(y),
                                repeat(smooth_x), repeat(smooth_y), [z_sin, z_cos])
            result = list(res)
            inter_sin = result[0]
            inter_cos = result[1]
        else:
            func_sin = scipy.interpolate.Rbf(x, y, z_sin, smooth=0, function="cubic")
            func_cos = scipy.interpolate.Rbf(x, y, z_cos, smooth=0, function="cubic")
            inter_sin = func_sin(smooth_x, smooth_y)
            inter_cos = func_cos(smooth_x, smooth_y)

        fig = plt.figure(figsize=(20, 15))
        plt.subplot(4, 1, 1)
        plt.title("Original sin")
        sns.lineplot(z_sin)

        plt.subplot(4, 1, 2)
        plt.title("Interpolated Sin")
        sns.lineplot(inter_sin)

        plt.subplot(4, 1, 3)
        plt.title("Original cos")
        sns.lineplot(z_cos)

        plt.subplot(4, 1, 4)
        plt.title("Interpolated Cos")
        sns.lineplot(inter_cos)

        cwd = os.getcwd()
        plts = os.path.join(cwd, 'logs/plots')
        if not os.path.isdir(plts):
            os.makedirs(plts)
        plt.savefig("logs/plots/seaborn_plot.png")
        time.sleep(1)
        plt.close(fig)
        plt.close('all')

    def expressions(self, emojis, data):
        with ThreadPoolExecutor(5) as executor:
            # worker = partial(self.show_exp, emojis=emojis)
            executor.map(self.show_exp, repeat(emojis), data)
        time.sleep(1)

    @staticmethod
    def rbf(x, y, x_inter, y_inter, inter):
        func = scipy.interpolate.Rbf(x, y, inter, smooth=0, function="cubic")
        interpolated = func(x_inter, y_inter)
        return interpolated
    
    @staticmethod
    def show_exp(emojis, value):
        rem = value % 3
        print(emojis[rem])
