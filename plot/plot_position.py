import matplotlib.pyplot as plt
from matplotlib import dates
from matplotlib import colors as mpcolors
from termcolor import colored
import numpy as np
import os
import pandas as pd
import sys
import logging
from typing import Tuple

from ampyutils import amutils
from plot import plot_utils
import am_config as amc

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def crdDiff(dMarker: dict, dfUTMh: pd.DataFrame, plotCrds: list, logger: logging.Logger) -> Tuple[pd.DataFrame, dict]:
    """
    calculates the differences of UTM,ellH using reference position or mean position
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # determine the difference to weighted average or marker position of UTM (N,E), ellH to plot
    dfCrd = pd.DataFrame(columns=plotCrds)

    # determine the coordinates of used reference (either mean or user determined)
    if [dMarker['UTM.E'], dMarker['UTM.N'], dMarker['ellH']] == [np.NaN, np.NaN, np.NaN]:
        # so no reference position given use mean position
        originCrds = [float(amc.dRTK['WAvg'][crd]) for crd in plotCrds]
    else:
        # make difference to reference position
        originCrds = [float(amc.dRTK['marker'][crd]) for crd in plotCrds]

    # subtract origin coordinates from UTMh positions
    dfCrd = dfUTMh.sub(originCrds, axis='columns')

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfCrd, dfName='dfCrd')

    crdMax = max(dfCrd.max())
    crdMin = min(dfCrd.min())
    crdMax = int(crdMax + (1 if crdMax > 0 else -1))
    crdMin = int(crdMin + (1 if crdMin > 0 else -1))

    dCrdLim = {'max': crdMax, 'min': crdMin}

    return dfCrd, dCrdLim


def markerAnnotation(coord: str, coordSD: str) -> str:
    """
    creates text to annotate with info about reference position
    """
    # cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # annotate each subplot with its reference position
    if [amc.dRTK['marker']['UTM.E'], amc.dRTK['marker']['UTM.N'], amc.dRTK['marker']['ellH']] == [np.NaN, np.NaN, np.NaN]:
        # use the mean UTM/ellH position for the reference point
        crdRef = amc.dRTK['WAvg'][coord]
        crdSD = amc.dRTK['WAvg'][coordSD]
        annotation = r'Mean: {refcrd:.3f}m ($\pm${stddev:.2f}m)'.format(refcrd=crdRef, stddev=crdSD)
    else:
        # we have a reference point
        crdRef = amc.dRTK['marker'][coord]
        crdOffset = amc.dRTK['marker'][coord] - amc.dRTK['WAvg'][coord]
        crdSD = amc.dRTK['WAvg'][coordSD]
        annotation = r'Ref: {crd:s} = {refcrd:.3f}m ({offset:.3f}m $\pm${stddev:.2f}m)'.format(crd=coord, refcrd=crdRef, stddev=crdSD, offset=crdOffset)

    return annotation


def plotUTMOffset(dRtk: dict, dfPos: pd.DataFrame, dfCrd: pd.DataFrame, dCrdLim: dict, logger: logging.Logger, showplot: bool = False):
    """
    plotUTMOffset plots the offset NEU wrt to reference point

    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # select colors for E, N, U coordinate difference
    colors = []
    colors.append([51 / 256., 204 / 256., 51 / 256.])
    colors.append([51 / 256., 51 / 256., 255 / 256.])
    colors.append([255 / 256., 51 / 256., 51 / 256.])

    # # determine the discrete colors for all observables
    # colormap = plt.cm.tab20  # I suggest to use nipy_spectral, Set1, Paired
    # colors = [colormap(i) for i in np.linspace(0, 1, 3)]
    # # print('colors = {!s}'.format(colors))

    # what to plot
    crds2Plot = ['UTM.E', 'UTM.N', 'ellH', 'ns']
    stdDev2Plot = ['sde', 'sdn', 'sdu']
    annotateList = ['east', 'north', 'ellh', '#SV']

    # find gaps in the data by comparing to mean value of difference in time
    dfPos['tDiff'] = dfPos['DT'].diff(1)
    dtMean = dfPos['tDiff'].mean()

    # look for it using location indexing
    dfPos.loc[dfPos['tDiff'] > dtMean, 'ns'] = np.nan

    amc.logDataframeInfo(df=dfPos, dfName='dfPos', callerName=cFuncName, logger=logger)

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig, ax = plt.subplots(nrows=len(crds2Plot), ncols=1, sharex=True, figsize=(20.0, 16.0))
    fig.suptitle('{syst:s} - {posf:s} - {date:s}'.format(posf=dRtk['info']['rtkPosFile'], syst=dRtk['syst'], date=dRtk['Time']['date']))

    # make title for plot
    ax[0].annotate('{syst:s} - {date:s}'.format(syst=dRtk['syst'], date=dfPos['DT'].iloc[0].strftime('%d %b %Y')), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='strong', fontsize='large')

    # copyright this
    ax[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='large')

    # subplots for coordinates display delta NEU
    for i, crd in enumerate(crds2Plot[:3]):
        axis = ax[i]

        # color for markers and alpha colors for error bars
        rgb = mpcolors.colorConverter.to_rgb(colors[i])
        rgb_new = amutils.make_rgb_transparent(rgb, (1, 1, 1), 0.3)

        # plot coordinate differences and error bars
        axis.errorbar(x=dfPos['DT'], y=dfCrd[crd], yerr=dfPos[stdDev2Plot[i]], linestyle='None', fmt='o', ecolor=rgb_new, capthick=1, markersize=1, color=colors[i])

        # set dimensions of y-axis
        axis.set_ylim([dCrdLim['min'], dCrdLim['max']])
        axis.set_ylabel('{crd:s} [m]'.format(crd=crd), fontsize='large', color=colors[i])

        # # annotate each subplot with its reference position
        annotatetxt = markerAnnotation(crd, stdDev2Plot[i])
        axis.annotate(annotatetxt, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='large')

        # title of sub-plot
        axis.set_title('{crd:s} offset'.format(crd=str.capitalize(annotateList[i]), fontsize='large'))

    # last subplot: number of satellites & PDOP
    for _, crd in enumerate(crds2Plot[3:4]):
        # plot #SVs on left axis
        axis = ax[-1]
        axis.set_ylim([0, 24])
        axis.set_ylabel('#SVs [-]', fontsize='large', color='grey')
        # axis.set_xlabel('Time [sec]', fontsize='large')

        axis.fill_between(dfPos['DT'], 0, dfPos['ns'], alpha=0.5, linestyle='-', linewidth=3, color='grey', label='#SVs', interpolate=False)
        # plot PDOP on second y-axis
        axRight = axis.twinx()

        axRight.set_ylim([0, 15])
        axRight.set_ylabel('PDOP [-]', fontsize='large', color='darkorchid')

        # plot PDOP value
        axRight.plot(dfPos['DT'], dfPos['PDOP'], linestyle='-', marker='.', markersize=1, color='darkorchid', label='PDOP')

        # set title
        axis.set_title('Visible satellites & PDOP', fontsize='large')

        # create the ticks for the time axis
        dtFormat = plot_utils.determine_datetime_ticks(startDT=dfPos['DT'].iloc[0], endDT=dfPos['DT'].iloc[-1])

        if dtFormat['minutes']:
            # axis.xaxis.set_major_locator(dates.MinuteLocator(byminute=range(10, 60, 10), interval=1))
            pass
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

    # save the plot in subdir png of GNSSSystem
    amutils.mkdir_p(os.path.join(dRtk['info']['dir'], 'png'))
    pngName = os.path.join(dRtk['info']['dir'], 'png', os.path.splitext(dRtk['info']['rtkPosFile'])[0] + '-ENU.png')
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    return
