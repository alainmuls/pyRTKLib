from matplotlib import colors as mpcolors
from matplotlib import dates
from matplotlib.dates import DayLocator, HourLocator, DateFormatter, drange
from termcolor import colored
from typing import Tuple
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys

from ampyutils import  amutils

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plot_rise_set_times(df_dt: pd.DataFrame, df_idx_rs: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_rise_set_times plots the rise/set times vs time per SVs as observed
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_dt, dfName='df_dt')

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig, ax = plt.subplots(figsize=(14.0, 10.0))
    fig.suptitle('rise set plot')

    # test
    for prn in df_idx_rs.index:
        # print('prn = {!s} type = {!s} len = {!s}'.format(prn, type(df_idx_rs.loc[prn]['idx_rise']), len(df_idx_rs.loc[prn]['idx_rise'])))

        for idx_rise, idx_set in zip(df_idx_rs.loc[prn]['idx_rise'], df_idx_rs.loc[prn]['idx_set']):
            # print('prn = {:s}: rise {!s}  set {!s}'.format(prn, idx_rise, idx_set))
            # print('prn = {:s}: rise {!s}  set {!s}'.format(prn, df_dt.loc[idx_rise].strftime('%H:%M:%S'), df_dt.loc[idx_set].strftime('%H:%M:%S')))

            y_prn = int(prn[1:]) - 1

            ax.plot_date([df_dt.loc[idx_rise], df_dt.loc[idx_set]], [y_prn, y_prn], linestyle='-')

    # format the date time ticks
    # matplotlib date format object
    hfmt = dates.DateFormatter('%d-%m %H')
    ax.xaxis.set_major_locator(dates.HourLocator(interval = 3))
    ax.xaxis.set_minor_locator(dates.HourLocator(interval = 1))
    ax.xaxis.set_major_formatter(hfmt)
    plt.xticks(rotation=30)

    # format the y-ticks to represent the PRN number
    plt.yticks(np.arange(0, 37))

    plt.show(block=True)
