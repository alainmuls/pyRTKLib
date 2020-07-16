import matplotlib.pyplot as plt
from termcolor import colored
import numpy as np
import os
import pandas as pd
import sys
import logging

from ampyutils import amutils
import am_config as amc

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plotUTMScatter(dRtk: dict, dfPos: pd.DataFrame, dfCrd: dict, dCrdLim: dict, logger: logging.Logger, showplot: bool = False):
    """
    plotUTMScatter plots scatter plot wrt reference position
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # select colors for E, N, U coordinate difference
    colors = []
    colors.append([51 / 256., 204 / 256., 51 / 256.])

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(11.0, 11.0))

    # make title for plot
    ax.annotate('UTM Scatter {syst:s} - {posf:s} - {date:s}'.format(syst=dRtk['syst'], posf=dRtk['info']['rtkPosFile'], date=dRtk['Time']['date']), xy=(0.5, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='center', verticalalignment='bottom', weight='strong', fontsize='xx-large')

    # copyright this
    ax.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -45), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')

    # annotate with reference position
    if [amc.dRTK['marker']['UTM.E'], amc.dRTK['marker']['UTM.N'], amc.dRTK['marker']['ellH']] == [np.NaN, np.NaN, np.NaN]:
        annotatePosRef = 'E = {east:.3f}, N = {north:.3f}'.format(east=amc.dRTK['WAvg']['UTM.E'], north=amc.dRTK['WAvg']['UTM.N'])
    else:
        annotatePosRef = 'E = {east:.3f}, N = {north:.3f}'.format(east=amc.dRTK['marker']['UTM.E'], north=amc.dRTK['marker']['UTM.N'])

    ax.annotate(annotatePosRef, xy=(0, 0), xycoords='axes fraction', xytext=(0, -45), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='strong', fontsize='medium')

    # draw circles for distancd evaluation on plot
    for radius in range(1, 15, 1):
        newCircle = plt.Circle((0, 0), radius, color='blue', fill=False, clip_on=True, alpha=0.4)
        ax.add_artist(newCircle)
        # annotate the radius for 1, 2, 5 and 10 meter
        # if radius in [1, 2, 3, 4, 5, 10]:
        ax.annotate('{radius:d}m'.format(radius=radius), xy=(np.pi / 4, radius), xytext=(np.pi / 4, radius), textcoords='polar', xycoords='polar', clip_on=True, color='blue', alpha=0.4)

    # get the marker styles
    markerBins = predefinedMarkerStyles()

    # go over all PDOP bins and plot according to the markersBin defined
    for i in range(len(dRtk['PDOP']['bins']) - 1, 0, -1):
        binInterval = 'bin{:d}-{:.0f}'.format(dRtk['PDOP']['bins'][i - 1], dRtk['PDOP']['bins'][i])
        index4Bin = (dfPos['PDOP'] > dRtk['PDOP']['bins'][i - 1]) & (dfPos['PDOP'] <= dRtk['PDOP']['bins'][i])

        ax.plot(dfCrd.loc[index4Bin, 'UTM.E'], dfCrd.loc[index4Bin, 'UTM.N'], label=r'{!s} $\leq$ PDOP $<$ {!s} ({:.1f}%)'.format(dRtk['PDOP']['bins'][i - 1], dRtk['PDOP']['bins'][i], dRtk['PDOP'][binInterval]['perc'] * 100), **markerBins[i])

    # lcoation of legend
    ax.legend(loc='best', markerscale=6)

    # add titles to axes
    ax.set_xlim([-7.5, +7.5])
    ax.set_ylim([-7.5, +7.5])
    ax.set_aspect(aspect='equal', adjustable='box')

    # nema the axis
    ax.set_xlabel('UTM East [m]', fontsize='large')
    ax.set_ylabel('UTM North [m]', fontsize='large')

    # save the plot in subdir png of GNSSSystem
    amutils.mkdir_p(os.path.join(dRtk['info']['dir'], 'png'))
    pngName = os.path.join(dRtk['info']['dir'], 'png', os.path.splitext(dRtk['info']['rtkPosFile'])[0] + '-scatter.png')
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)


def plotUTMScatterBin(dRtk: dict, dfPos: pd.DataFrame, dfCrd: dict, dCrdLim: dict, logger: logging.Logger, showplot: bool = False):
    """
    plotUTMScatter plots scatter plot (per DOPbin)
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # select colors for E, N, U coordinate difference
    colors = []
    colors.append([51 / 256., 204 / 256., 51 / 256.])

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig, ax = plt.subplots(nrows=2, ncols=3, figsize=(16.0, 11.0))

    # make title for plot
    fig.suptitle('UTM Scatter {syst:s} - {posf:s} - {date:s}'.format(syst=dRtk['syst'], posf=dRtk['info']['rtkPosFile'], date=dRtk['Time']['date']), weight='strong', fontsize='xx-large')

    # copyright this
    ax[1][2].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -90), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='medium')

    # annotate with reference position
    if [amc.dRTK['marker']['UTM.E'], amc.dRTK['marker']['UTM.N'], amc.dRTK['marker']['ellH']] == [np.NaN, np.NaN, np.NaN]:
        annotatePosRef = 'E = {east:.3f}, N = {north:.3f}'.format(east=amc.dRTK['WAvg']['UTM.E'], north=amc.dRTK['WAvg']['UTM.N'])
    else:
        annotatePosRef = 'E = {east:.3f}, N = {north:.3f}'.format(east=amc.dRTK['marker']['UTM.E'], north=amc.dRTK['marker']['UTM.N'])

    ax[1][0].annotate(annotatePosRef, xy=(0, 0), xycoords='axes fraction', xytext=(0, -90), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='strong', fontsize='medium')

    # get the marker styles
    markerBins = predefinedMarkerStyles()

    # go over all PDOP bins and plot according to the markersBin defined
    for i in range(0, len(dRtk['PDOP']['bins']) - 1):
        binInterval = 'bin{:d}-{:.0f}'.format(dRtk['PDOP']['bins'][i], dRtk['PDOP']['bins'][i + 1])
        index4Bin = (dfPos['PDOP'] > dRtk['PDOP']['bins'][i]) & (dfPos['PDOP'] <= dRtk['PDOP']['bins'][i + 1])

        # print('index4Bin = {!s}'.format(np.sum(index4Bin)))
        lblBin = r'{!s} $\leq$ PDOP $<$ {!s} ({:.1f}%, #{:d})'.format(dRtk['PDOP']['bins'][i], dRtk['PDOP']['bins'][i + 1], dRtk['PDOP'][binInterval]['perc'] * 100, np.sum(index4Bin))
        logger.info('{func:s}: {bin:s}'.format(func=cFuncName, bin=lblBin))

        # get the axis
        axis = ax[i // 3][i % 3]

        # plot per dopBin
        axis.plot(dfCrd.loc[index4Bin, 'UTM.E'], dfCrd.loc[index4Bin, 'UTM.N'], label=lblBin, **markerBins[i + 1])

        # draw circles for distancd evaluation on plot
        for radius in range(1, 15, 1):
            newCircle = plt.Circle((0, 0), radius, color='blue', fill=False, clip_on=True, alpha=0.4)
            axis.add_artist(newCircle)
            # annotate the radius for 1, 2, 5 and 10 meter
            # if radius in [1, 2, 3, 4, 5, 10]:
            axis.annotate('{radius:d}m'.format(radius=radius), xy=(np.pi / 4, radius), xytext=(np.pi / 4, radius), textcoords='polar', xycoords='polar', clip_on=True, color='blue', alpha=0.4)

        # lcoation of legend
        axis.legend(loc='best', markerscale=6)

        # add titles to axes
        axis.set_xlim([-7.5, +7.5])
        axis.set_ylim([-7.5, +7.5])
        axis.set_aspect(aspect='equal', adjustable='box')

        # nema the axis
        axis.set_xlabel('UTM East [m]', fontsize='large')
        axis.set_ylabel('UTM North [m]', fontsize='large')

    # save the plot in subdir png of GNSSSystem
    amutils.mkdir_p(os.path.join(dRtk['info']['dir'], 'png'))
    pngName = os.path.join(dRtk['info']['dir'], 'png', os.path.splitext(dRtk['info']['rtkPosFile'])[0] + '-scatter-bin.png')
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)


def predefinedMarkerStyles() -> list:
    """
    predefined markerstyles for plotting
    Returns: markerBins used for coloring as function of DOP bin
    """
    # # plot the centerpoint and circle
    marker_style_center = dict(linestyle='', color='red', markersize=5, marker='^', markeredgecolor='red', alpha=0.75)
    marker_style_doplt2 = dict(linestyle='', color='green', markersize=2, marker='.', markeredgecolor='green', alpha=0.30)
    marker_style_doplt3 = dict(linestyle='', color='orange', markersize=2, marker='.', markeredgecolor='orange', alpha=0.45)
    marker_style_doplt4 = dict(linestyle='', color='blue', markersize=2, marker='.', markeredgecolor='blue', alpha=0.60)
    marker_style_doplt5 = dict(linestyle='', color='purple', markersize=2, marker='.', markeredgecolor='purple', alpha=0.75)
    marker_style_doplt6 = dict(linestyle='', color='red', markersize=2, marker='.', markeredgecolor='red', alpha=0.90)
    marker_style_doprest = dict(linestyle='', color='black', markersize=2, marker='.', markeredgecolor='black', alpha=0.90)

    markerBins = [marker_style_center, marker_style_doplt2, marker_style_doplt3, marker_style_doplt4, marker_style_doplt5, marker_style_doplt6, marker_style_doprest]

    return markerBins
