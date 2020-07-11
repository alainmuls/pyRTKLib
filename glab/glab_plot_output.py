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
from glab import glab_constants as glc

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plot_glab_position(dfCrd: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_glab_position plots the position difference wrt to Nominal a priori position
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # select colors for E, N, U coordinate difference
    colors = []
    colors.append([51 / 256., 204 / 256., 51 / 256.])
    colors.append([51 / 256., 51 / 256., 255 / 256.])
    colors.append([255 / 256., 51 / 256., 51 / 256.])

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig, ax = plt.subplots(nrows=4, ncols=1, sharex=True, figsize=(20.0, 16.0))
    # fig.suptitle('{syst:s} - {posf:s} - {date:s}'.format(posf=dRtk['info']['rtkPosFile'], syst=dRtk['syst'], date=dRtk['Time']['date']))
    fig.suptitle('gLABng {out:s}'.format(out=amc.dRTK['glab_out']))

    # make title for plot
    ax[0].annotate('{syst:s} - {date:s}'.format(syst='COMB', date='14 Mai 2019'), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='strong', fontsize='large')

    # copyright this
    ax[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='large')

    # get max/min values of the columns glc.dgLab['OUTPUT']['plot']['dENU']
    crd_mean = {}

    for crd in glc.dgLab['OUTPUT']['plot']['dENU']:
        # get max/min for this crd and the previous ones
        crd_mean[crd] = dfCrd[crd].mean()
        # crd_max = max(dfCrd[crd].max(), crd_max)
        # crd_min = min(dfCrd[crd].min(), crd_min)

    # same values all the time
    # crd_max = 5
    # crd_min = -crd_max

    # plot the ENU difference xwrt nominal initial position and display the standard deviation, xDOP
    for i, (crd, sdCrd) in enumerate(zip(glc.dgLab['OUTPUT']['plot']['dENU'], glc.dgLab['OUTPUT']['plot']['sdENU'])):
        # select the axis to use for this coordinate
        axis = ax[i]

        # color for markers and alpha colors for error bars
        rgb = mpcolors.colorConverter.to_rgb(colors[i])
        rgb_alpha = amutils.make_rgb_transparent(rgb, (1, 1, 1), 0.3)

        # plot coordinate differences and error bars
        axis.errorbar(x=dfCrd['Time'].values, y=dfCrd[crd], yerr=dfCrd[sdCrd], linestyle='-', fmt='o', ecolor=rgb_alpha, capthick=1, markersize=1, color=colors[i])

        # set dimensions of y-axis
        axis.set_ylim([crd_mean[crd] - 5, crd_mean[crd] + 5])
        axis.set_ylabel('{crd:s} [m]'.format(crd=crd, fontsize='large'), color=colors[i])

        # # annotate each subplot with its reference position
        # annotatetxt = markerAnnotation(crd, sdCrd)
        # axis.annotate(annotatetxt, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='large')

        # title of sub-plot
        # axis.set_title('{crd:s} offset'.format(crd=str.capitalize(crd), fontsize='large'))

    # last subplot: number of satellites & PDOP
    # plot #SVs on left axis
    axis = ax[-1]
    axis.set_ylim([0, 24])
    axis.set_ylabel('#SVs [-]', fontsize='large', color='grey')
    # axis.set_xlabel('Time [sec]', fontsize='large')

    axis.fill_between(dfCrd['Time'].values, 0, dfCrd['#SVs'], alpha=0.5, linestyle='-', linewidth=3, color='grey', label='#SVs', interpolate=False)

    # plot PDOP on second y-axis
    axis_right = axis.twinx()

    axis_right.set_ylim([0, 15])
    axis_right.set_ylabel('PDOP [-]', fontsize='large', color='darkorchid')

    # plot PDOP value
    axis_right.plot(dfCrd['Time'], dfCrd['PDOP'], linestyle='-', marker='.', markersize=1, color='darkorchid', label='PDOP')

    # set title
    axis.set_title('Visible satellites & PDOP', fontsize='large')

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    return
