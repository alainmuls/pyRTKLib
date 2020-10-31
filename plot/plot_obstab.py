from matplotlib import dates
from termcolor import colored
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import sys
import matplotlib.ticker as ticker
from typing import Tuple

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
    prn_colors, title_font = amutils.create_colormap_font(nrcolors=max_prn, font_size=12)

    # subplots
    fig, ax = plt.subplots(figsize=(16.0, 10.0))
    print(amc.dRTK['rnx']['times'])
    fig.suptitle('Rise/Set for {gnss:s} - {marker:s} - {date:s}'.format(gnss=amc.dRTK['rnx']['gnss'][gnss]['name'], marker=amc.dRTK['rnx']['gnss'][gnss]['marker'], date='{date:s} ({yy:02d}/{doy:03d})'.format(date=amc.dRTK['rnx']['times']['DT'][:10], yy=amc.dRTK['rnx']['times']['yy'], doy=amc.dRTK['rnx']['times']['doy'])), fontdict=title_font, fontsize=24)

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


def plot_rise_set_stats(gnss: str, df_arcs: pd.DataFrame, nr_arcs: int, logger: logging.Logger, showplot: bool = False):
    """
    plot_rise_set_stats plots the rise/set statistics per SVs
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    logger.info('{func:s}: plotting observation statistics'.format(func=cFuncName))
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_dt, dfName='df_dt')

    # set up the plot
    plt.style.use('ggplot')
    # plt.style.use('seaborn-darkgrid')

    dx_obs, dx_tle, arc_width = bars_info(nr_arcs=nr_arcs, logger=logger)

    # create colormap with 36 discrete colors
    arc_colors, title_font = amutils.create_colormap_font(nrcolors=nr_arcs, font_size=12)

    x = np.arange(df_arcs.shape[0])  # the label locations

    # subplots
    fig, (ax1, ax2) = plt.subplots(figsize=(14.0, 9.0), nrows=2)
    fig.suptitle('Rise/Set for {gnss:s} - {marker:s} - {date:s}'.format(gnss=amc.dRTK['rnx']['gnss'][gnss]['name'], marker=amc.dRTK['rnx']['gnss'][gnss]['marker'], date='{date:s} ({yy:02d}/{doy:03d})'.format(date=amc.dRTK['rnx']['times']['DT'][:10], yy=amc.dRTK['rnx']['times']['yy'], doy=amc.dRTK['rnx']['times']['doy'])), fontdict=title_font, fontsize=24)

    # creating bar plots for absolute values
    for i_arc, (obs_dx, tle_dx) in enumerate(zip(dx_obs, dx_tle)):
        ax1.bar(x + tle_dx, df_arcs['Arc{arc:d}_tle'.format(arc=i_arc)], width=arc_width, color=arc_colors[i_arc], alpha=0.35, edgecolor='black', hatch='//', label='TLE Arc {arc:d}'.format(arc=i_arc))
        ax1.bar(x + obs_dx, df_arcs['Arc{arc:d}_obs'.format(arc=i_arc)], width=arc_width, color=arc_colors[i_arc], label='Obs Arc {arc:d}'.format(arc=i_arc))

    # beautify plot
    ax1.xaxis.grid()
    ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    # ax1.set_xlabel('PRN', fontdict=title_font)
    ax1.set_ylabel('#Observed / #Predicted', fontdict=title_font)

    # setticks on X axis to represent the PRN
    ax1.xaxis.set_ticks(np.arange(0, df_arcs.shape[0], 1))
    ax1.xaxis.set_major_formatter(ticker.FormatStrFormatter('%0.0f'))
    ax1.set_xticklabels(df_arcs['PRN'], rotation=90)

    # # creating bar plots for relative values
    for i_arc, (obs_dx, tle_dx) in enumerate(zip(dx_obs, dx_tle)):
        ax2.bar(x + tle_dx, (df_arcs['Arc{arc:d}_%'.format(arc=i_arc)] * 100), width=arc_width, color=arc_colors[i_arc], label='Perc Arc {arc:d}'.format(arc=i_arc))

        # write the percentage in the bars
        for i, patch in enumerate(ax2.patches[i_arc * df_arcs.shape[0]:]):
            if not np.isnan(df_arcs.iloc[i]['Arc{arc:d}_%'.format(arc=i_arc)]):
                ax2.text(patch.get_x(), patch.get_y() + 2, '{rnd:.1f}%'.format(rnd=(df_arcs.iloc[i]['Arc{arc:d}_%'.format(arc=i_arc)] * 100)), fontsize=8, rotation=90, color='black', verticalalignment='bottom')

    # beautify plot
    ax2.xaxis.grid()
    ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5))

    ax2.set_xlabel('PRN', fontdict=title_font)
    ax2.set_ylabel('Percentage', fontdict=title_font)

    # setticks on X axis to represent the PRN
    ax2.xaxis.set_ticks(np.arange(0, df_arcs.shape[0], 1))
    ax2.xaxis.set_major_formatter(ticker.FormatStrFormatter('%0.0f'))
    ax2.set_xticklabels(df_arcs['PRN'], rotation=90)

    # save the plot in subdir png of GNSSSystem
    png_dir = os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker'], 'png')
    amutils.mkdir_p(png_dir)
    pngName = os.path.join(png_dir, os.path.splitext(amc.dRTK['rnx']['gnss'][gnss]['obstab'])[0] + '-obs.png')
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    plt.show()


def bars_info(nr_arcs: int, logger:logging.Logger) -> Tuple[list, list, int]:
    """
    bars_info determines the width of an individual bar, the spaces between the arc bars, and localtion in delta-x-coordinates of beginning of each PRN arcs
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    logger.info('{func:s}: determining the information for the bars'.format(func=cFuncName))

    # the bars for all arcs for 1 PRN may span over 0.8 units (from [-0.4 => 0.4]), including the spaces between the different arcs
    width_prn_arcs = 0.8
    dx_start = -0.4  # start of the bars relative to integer of PRN
    width_space = 0.1  # space between the different arcs for 1 PRN

    # substract width-spaces needed for nr_arcs
    width_arcs = width_prn_arcs - (nr_arcs - 1) * width_space

    # the width taken by 1 arc for 1 prn is
    width_arc = width_arcs / nr_arcs

    # each arc has up to 2 bars which partial overlap
    width_bar = width_arc * 0.75

    # get the delta-x to apply to the integer value that corresponds to a PRN
    dx_obs = [dx_start + i * (width_space + width_arc) for i in np.arange(nr_arcs)]
    dx_tle = [obs_dx + width_bar * 0.25 for obs_dx in dx_obs]

    return dx_obs, dx_tle, width_arc
