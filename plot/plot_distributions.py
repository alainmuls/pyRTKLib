import matplotlib
import matplotlib.pyplot as plt
from termcolor import colored
import numpy as np
import os
import pandas as pd
import sys
import logging
from matplotlib.ticker import FixedLocator
from matplotlib.gridspec import GridSpec
from matplotlib import dates

from pandas.plotting import register_matplotlib_converters
from ampyutils import amutils
from plot import plot_utils

register_matplotlib_converters()

__author__ = 'amuls'


def plot_enu_distribution(dRtk: dict, dfENUdist: pd.DataFrame, dfENUstat: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_enu_distribution plots the distribution for the ENU coordinates
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: creating ENU distribution plot'.format(func=cFuncName))

    # select colors for E, N, U coordinate difference
    colors = []
    colors.append([51 / 256., 204 / 256., 51 / 256.])
    colors.append([51 / 256., 51 / 256., 255 / 256.])
    colors.append([255 / 256., 51 / 256., 51 / 256.])

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig, ax = plt.subplots(nrows=1, ncols=4, sharex=True, sharey=True, figsize=(24.0, 10.0))
    fig.suptitle('{syst:s} - {posf:s} - {date:s}: ENU Statistics'.format(posf=dRtk['info']['rtkPosFile'], syst=dRtk['syst'], date=dRtk['Time']['date']))

    # the indexes on the x-axis
    ind = np.arange(len(dfENUdist.index))

    for axis, crd, color in zip(ax[:3], ('dUTM.E', 'dUTM.N', 'dEllH'), colors):
        axis.bar(ind, dfENUdist[crd], alpha=0.5, color=color, edgecolor='none')
        # rotate the ticks on this axis
        axis.set_xticklabels(dfENUdist.index.tolist(), rotation='vertical')
        # set th etitle for sub-plot
        axis.set_title(label=crd, color=color, fontsize='large')

        # annotate the plot with the statistics calculated
        axis.annotate(r'Mean = {:.3f}'.format(dfENUstat.loc['mean', crd]), xy=(1, 1), xycoords='axes fraction', xytext=(0, -25), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')
        axis.annotate(r'$\sigma$ = {:.3f}'.format(dfENUstat.loc['std', crd]), xy=(1, 1), xycoords='axes fraction', xytext=(0, -45), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')

    # add the 3 distributions on 1 subplot for comparing
    width = .25
    for i, crd, color in zip((-1, 0, +1), ('dUTM.E', 'dUTM.N', 'dEllH'), colors):
        ax[-1].bar(ind - (i * width), dfENUdist[crd], width=width, alpha=0.5, color=color, edgecolor='none')
        # rotate the ticks on this axis
        ax[-1].set_xticklabels(dfENUdist.index.tolist(), rotation='vertical')

    # set the ticks on the x-axis
    ax[0].set_xlim([ind[0], ind[-1]])
    ax[0].xaxis.set_major_locator(FixedLocator(ind))

    # copyright this
    ax[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 1), xycoords='axes fraction', xytext=(0, +25), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')

    # save the plot in subdir png of GNSSSystem
    amutils.mkdir_p(os.path.join(dRtk['info']['dir'], 'png'))
    pngName = os.path.join(dRtk['info']['dir'], 'png', os.path.splitext(dRtk['info']['rtkPosFile'])[0] + '-ENU-dist.png')
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    return


def plot_xdop_distribution(dRtk: dict, dfXDOP: pd.DataFrame, dfXDOPdisp: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_xdop_distribution plots the XDOP values and the distribution XDOPs
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: creating XDOP distribution plot'.format(func=cFuncName))

    # select colors for xDOP coordinate difference
    colors = ('blue', 'green', 'cyan', 'red')

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig = plt.figure(figsize=(24.0, 14.0), tight_layout=True)
    fig.suptitle('{syst:s} - {posf:s} - {date:s}: XDOP'.format(posf=dRtk['info']['rtkPosFile'], syst=dRtk['syst'], date=dRtk['Time']['date']))

    # create a grid for lotting the XDOP line plots and 6 XDOP distribution plots
    gs = GridSpec(2, 4)

    # plot the XDOPs and #SVs on the first axis
    ax = fig.add_subplot(gs[0, :])  # first row, span all columns
    plot_xdop_svs(dfDops=dfXDOP, colors=colors, axis=ax)

    # add the xDOP distributions
    for col, xdop, color in zip((0, 1, 2, 3), dfXDOPdisp.columns[-4:], colors):
        # create exis for this figure
        ax = fig.add_subplot(gs[1, col])

, sharey=ax1

        # plot distribution for a DOP value
        plot_xdop_histogram(dfDopsDist=dfXDOPdisp, xdop=xdop, color=color, axis=ax)

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    sys.exit(55555555)


def plot_xdop_svs(dfDops: pd.DataFrame, colors: tuple, axis):
    """
    plot_xdop_svs plots the XDOP curves and #SVs on a given axis
    """
    axis.set_ylim([0, 24])
    axis.set_ylabel('#SVs [-]', fontsize='large', color='grey')
    # axis.set_xlabel('Time [sec]', fontsize='large')

    axis.fill_between(dfDops['DT'], 0, dfDops['#SVs'], alpha=0.5, linestyle='-', linewidth=3, color='grey', label='#SVs', interpolate=False)
    # plot PDOP on second y-axis
    axRight = axis.twinx()

    axRight.set_ylim([0, 15])
    axRight.set_ylabel('XDOP [-]', fontsize='large')

    # plot XDOPs (last 4 columns)
    for dop, color in zip(dfDops.columns[-4:], colors):
        axRight.plot(dfDops['DT'], dfDops[dop], linestyle='-', marker='.', markersize=1, color=color, label=dop)

    # set title
    axis.set_title('Visible satellites & XDOP', fontsize='x-large')

    # create the ticks for the time axis
    dtFormat = plot_utils.determine_datetime_ticks(startDT=dfDops['DT'].iloc[0], endDT=dfDops['DT'].iloc[-1])

    if dtFormat['minutes']:
        axis.xaxis.set_major_locator(dates.MinuteLocator(byminute=range[1, 60, 5], interval=1))
    else:
        axis.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every 4 hours
    axis.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

    axis.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
    axis.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))

    axis.xaxis.set_tick_params(rotation=0)
    for tick in axis.xaxis.get_major_ticks():
        # tick.tick1line.set_markersize(0)
        # tick.tick2line.set_markersize(0)
        tick.label1.set_horizontalalignment('center')


def plot_xdop_histogram(dfDopsDist: pd.DataFrame, xdop: str, color: tuple, axis):
    """
    plot_xdop_histogram plots the histogram for the specified xDOP
    """
    # the indexes on the x-axis
    ind = np.arange(len(dfDopsDist.index))

    print('ind = {!s}'.format(ind))
    print('dfDopsDist.index.tolist() = {!s}'.format(dfDopsDist.index.tolist()))

    axis.bar(ind, dfDopsDist[xdop], alpha=0.5, color=color, edgecolor='none')
    # rotate the ticks on this axis
    axis.set_xticklabels(dfDopsDist.index.tolist(), rotation='vertical')
    # set th etitle for sub-plot
    axis.set_title(label=xdop, color=color, fontsize='large')
