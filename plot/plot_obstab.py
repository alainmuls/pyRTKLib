from matplotlib import dates
from termcolor import colored
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys
import matplotlib._color_data as mcd
import matplotlib.markers

import am_config as amc
from ampyutils import amutils

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plot_rise_set_times(gnss: str, df_dt: pd.DataFrame, df_rs: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_rise_set_times plots the rise/set times vs time per SVs as observed
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    logger.info('{func:s}: plotting rise/set times'.format(func=cFuncName))
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_dt, dfName='df_dt')

    # set up the plot
    plt.style.use('ggplot')
    # plt.style.use('seaborn-darkgrid')

    # create colormap with 36 discrete colors
    max_prn = 36
    # colormap = amcolormap.discrete_cmap(max_prn, 'cubehelix')

    font = {'family': 'serif',
            # 'color': 'darkred',
            'weight': 'bold',
            'size': 14,
            }

    # get the color names
    color_names = [name for name in mcd.XKCD_COLORS]
    color_step = len(color_names) // max_prn
    color_used = color_names[::color_step]
    # colormap = [mcd.CSS4_COLORS[name] for name in mcd.CSS4_COLORS]

    # colormap = amcolormap.discrete_cmap(max_prn)
    # the value on the y-axis for this SV
    # prn_y = range(0, max_prn)
    # prn_rgba = [colormap(y / max_prn) for y in prn_y]

    # subplots
    fig, ax = plt.subplots(figsize=(14.0, 10.0))
    fig.suptitle('Rise Set for system {gnss:s} on {date:s}'.format(gnss=amc.dRTK['rnx']['gnss'][gnss]['name'], date='{yy:02d}/{doy:03d}'.format(yy=amc.dRTK['rnx']['times']['yy'], doy=amc.dRTK['rnx']['times']['doy'])), fontdict=font, fontsize=24)

    # draw the rise to set lines per PRN
    for prn in df_rs.index:
        y_prn = int(prn[1:])

        # get the lists with rise / set times as observed
        for dt_obs_rise, dt_obs_set in zip(df_rs.loc[prn]['obs_rise'], df_rs.loc[prn]['obs_set']):
            ax.plot_date([dt_obs_rise, dt_obs_set], [y_prn, y_prn], linestyle='solid', color=color_used[y_prn], linewidth=2, marker='v', markersize=4, alpha=1)

        # get the lists with rise / set times by TLEs
        for dt_tle_rise, dt_tle_set, dt_tle_cul in zip(df_rs.loc[prn]['tle_rise'], df_rs.loc[prn]['tle_set'], df_rs.loc[prn]['tle_cul']):
            ax.plot_date([dt_tle_rise, dt_tle_set], [y_prn - 0.25, y_prn - 0.25], linestyle='--', color=color_used[y_prn], linewidth=2, marker='^', markersize=4, alpha=0.5)

            # add a indicator for the culmination time of PRN
            ax.plot(dt_tle_cul, y_prn - 0.25, marker='d', markersize=4, alpha=0.5, color=color_used[y_prn])

    # format the date time ticks
    ax.xaxis.set_major_locator(dates.DayLocator(interval=1))
    ax.xaxis.set_major_formatter(dates.DateFormatter('\n%d-%m-%Y'))

    ax.xaxis.set_minor_locator(dates.HourLocator(interval=3))
    ax.xaxis.set_minor_formatter(dates.DateFormatter('%H:%M'))
    plt.xticks()

    # format the y-ticks to represent the PRN number
    plt.yticks(np.arange(0, max_prn + 1))
    prn_ticks = [''] * max_prn

    # get list of observed PRN numbers (without satsyst letter)
    prn_nrs = [int(prn[1:]) for prn in df_rs.index]

    # and the corresponding ticks
    for prn_nr, prn_txt in zip(prn_nrs, df_rs.index):
        prn_ticks[prn_nr] = prn_txt

    # adjust color for y ticks
    for color, tick in zip(color_used, ax.yaxis.get_major_ticks()):
        tick.label1.set_color(color)  # set the color property
        tick.label1.set_fontweight('bold')
    ax.set_yticklabels(prn_ticks)

    # set the axis labels
    ax.set_xlabel('Time', fontdict=font)
    ax.set_ylabel('PRN', fontdict=font)

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
