from matplotlib import dates
from termcolor import colored
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys

import am_config as amc
from ampyutils import amutils

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plot_rise_set_times(gnss: str, df_rs: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_rise_set_times plots the rise/set times vs time per SVs as observed / predicted
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    logger.info('{func:s}: plotting rise/set times'.format(func=cFuncName))
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_dt, dfName='df_dt')

    # set up the plot
    plt.style.use('ggplot')
    # plt.style.use('seaborn-darkgrid')

    # create colormap with 36 discrete colors
    max_prn = 36
    prn_colors, title_font = amutils.create_colormap_font(nrcolors=max_prn, font_size=14)

    # subplots
    fig, ax = plt.subplots(figsize=(16.0, 10.0))
    fig.suptitle('Rise Set for system {gnss:s} on {date:s}'.format(gnss=amc.dRTK['rnx']['gnss'][gnss]['name'], date='{yy:02d}/{doy:03d}'.format(yy=amc.dRTK['rnx']['times']['yy'], doy=amc.dRTK['rnx']['times']['doy'])), fontdict=title_font, fontsize=24)

    # draw the rise to set lines per PRN
    for prn in df_rs.index:
        y_prn = int(prn[1:]) - 1

        # get the lists with rise / set times as observed
        for dt_obs_rise, dt_obs_set in zip(df_rs.loc[prn]['obs_rise'], df_rs.loc[prn]['obs_set']):
            ax.plot_date([dt_obs_rise, dt_obs_set], [y_prn, y_prn], linestyle='solid', color=prn_colors[y_prn], linewidth=2, marker='v', markersize=4, alpha=1)

        # get the lists with rise / set times by TLEs
        for dt_tle_rise, dt_tle_set, dt_tle_cul in zip(df_rs.loc[prn]['tle_rise'], df_rs.loc[prn]['tle_set'], df_rs.loc[prn]['tle_cul']):
            ax.plot_date([dt_tle_rise, dt_tle_set], [y_prn - 0.25, y_prn - 0.25], linestyle='--', color=prn_colors[y_prn], linewidth=2, marker='^', markersize=4, alpha=0.5)

            # add a indicator for the culmination time of PRN
            ax.plot(dt_tle_cul, y_prn - 0.25, marker='d', markersize=4, alpha=0.5, color=prn_colors[y_prn])

    # format the date time ticks
    ax.xaxis.set_major_locator(dates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(dates.DateFormatter('\n%d-%m-%Y'))

    ax.xaxis.set_minor_locator(dates.HourLocator(interval=3))
    ax.xaxis.set_minor_formatter(dates.DateFormatter('%H:%M'))
    plt.xticks()

    # format the y-ticks to represent the PRN number
    plt.yticks(np.arange(0, max_prn))
    prn_ticks = [''] * max_prn

    # get list of observed PRN numbers (without satsyst letter)
    prn_nrs = [int(prn[1:]) for prn in df_rs.index]

    # and the corresponding ticks
    for prn_nr, prn_txt in zip(prn_nrs, df_rs.index):
        prn_ticks[prn_nr - 1] = prn_txt

    # adjust color for y ticks
    for color, tick in zip(prn_colors, ax.yaxis.get_major_ticks()):
        tick.label1.set_color(color)  # set the color property
        tick.label1.set_fontweight('bold')
    ax.set_yticklabels(prn_ticks)

    # set the axis labels
    ax.set_xlabel('Time', fontdict=title_font)
    ax.set_ylabel('PRN', fontdict=title_font)

    # save the plot in subdir png of GNSSSystem
    png_dir = os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker'], 'png')
    amutils.mkdir_p(png_dir)
    pngName = os.path.join(png_dir, os.path.splitext(amc.dRTK['rnx']['gnss'][gnss]['obstab'])[0] + '-RS.png')
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)


def plot_rise_set_stats(gnss: str, df_rs: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_rise_set_stats plots the rise/set statistics per SVs
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    logger.info('{func:s}: plotting observation statistics'.format(func=cFuncName))
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_dt, dfName='df_dt')

    # set up the plot
    plt.style.use('ggplot')
    # plt.style.use('seaborn-darkgrid')

    # create colormap with 36 discrete colors
    max_prn = 36
    prn_colors, title_font = amutils.create_colormap_font(nrcolors=max_prn, font_size=14)

    # subplots
    fig, (ax1, ax2) = plt.subplots(figsize=(16.0, 10.0), nrows=2)
    fig.suptitle('Rise Set statistics for system {gnss:s} on {date:s}'.format(gnss=amc.dRTK['rnx']['gnss'][gnss]['name'], date='{yy:02d}/{doy:03d}'.format(yy=amc.dRTK['rnx']['times']['yy'], doy=amc.dRTK['rnx']['times']['doy'])), fontdict=title_font, fontsize=24)

    # # make the plot with absolute values
    # # draw the rise to set lines per PRN
    # for prn in df_rs.index:
    #     y_prn = int(prn[1:])
    #     for obs_count, tle_count in zip(df_rs.loc[prn]['obs_arc_count'], df_rs.loc[prn]['tle_arc_count']):
    #         print('{prn:s}: {obs:d} {tle:d}'.format(prn=prn, obs=obs_count, tle=int(tle_count)))

    #     print('longest obs = {!s}'.format(longest(df_rs.loc[prn]['obs_arc_count'])))
    #     print('longest tle = {!s}'.format(longest(df_rs.loc[prn]['tle_arc_count'])))


def longest(a):
    return max(len(a), *map(longest, a)) if isinstance(a, list) and a else 0





    # df = pd.DataFrame({'a': a, 'b': b, 'c': c, 'd': d}, columns=['a', 'b', 'c', 'd'])
    # df.set_index('a', inplace=True)

    # df.plot.bar()
    # plt.show()
