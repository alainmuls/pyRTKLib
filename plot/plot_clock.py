import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time
import numpy as np
import os
import pandas as pd
import sys
from termcolor import colored
from matplotlib import dates
import logging
import am_config as amc

from ampyutils import amutils
from rnx2rtkp import rtklibconstants
from plot import plot_utils


def plotClock(dfClk: pd.DataFrame, dRtk: dict, logger: logging.Logger, showplot: bool = False):
    """
    plotClock plots athe clock for all systems
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # set up the plot
    plt.style.use('ggplot')
    colors = ['blue', 'red', 'green', 'black']

    amc.logDataframeInfo(df=dfClk, dfName='dfClk', callerName=cFuncName, logger=logger)

    # find out for which system we have clk offset values
    GNSSSysts = []
    for gnss in ['GAL', 'GPS', 'OTH', 'GLO']:
        if dfClk[gnss].any():
            GNSSSysts.append(gnss)
    logger.info('{func:s}: Clock available for GNSS systems {syst:s}'.format(func=cFuncName, syst=' '.join(GNSSSysts)))

    # create the plot araea
    fig, axis = plt.subplots(nrows=len(GNSSSysts), ncols=1, figsize=(24.0, 20.0))

    for i, GNSSsyst in enumerate(GNSSSysts):
        logger.info('{func:s}: plotting clock offset for {syst:s}'.format(func=cFuncName, syst=GNSSsyst))

        # get the axis to draw to
        if len(GNSSSysts) == 1:
            ax = axis
        else:
            ax = axis[i]

        # create the plot for this GNSS system
        dfClk.plot(ax=ax, x='DT', y=GNSSsyst, marker='.', linestyle='', color=colors[i])

        # create the ticks for the time axis
        dtFormat = plot_utils.determine_datetime_ticks(startDT=dfClk['DT'].iloc[0], endDT=dfClk['DT'].iloc[-1])

        if dtFormat['minutes']:
            ax.xaxis.set_major_locator(dates.MinuteLocator(byminute=[0,15,30,45], interval = 1))
        else:
            ax.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every 4 hours
        ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

        ax.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
        ax.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))

        ax.xaxis.set_tick_params(rotation=0)
        for tick in ax.xaxis.get_major_ticks():
            # tick.tick1line.set_markersize(0)
            # tick.tick2line.set_markersize(0)
            tick.label1.set_horizontalalignment('center')

        # name the axis
        ax.set_ylabel('{syst:s} Clock Offset [ns]'.format(syst=GNSSsyst), fontsize='large', color=colors[i])
        ax.set_xlabel('Time', fontsize='large')

        # title of sub-plot
        ax.set_title('Clock offset relative to {syst:s} @ {date:s}'.format(syst=GNSSsyst, date=dfClk['DT'].iloc[0].strftime('%d %b %Y'), fontsize='large'))

    # save the plot in subdir png of GNSSSystem
    amutils.mkdir_p(os.path.join(dRtk['info']['dir'], 'png'))
    pngName = os.path.join(dRtk['info']['dir'], 'png', os.path.splitext(dRtk['info']['rtkPosFile'])[0] + '-CLK.png')
    # print('pngName = {:s}'.format(pngName))
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)
