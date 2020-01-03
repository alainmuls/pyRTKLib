import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from termcolor import colored
import numpy as np
import os
import pandas as pd
import sys
import logging
from matplotlib.ticker import MultipleLocator, FixedLocator

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plot_enu_distribution(dRtk, dfENUdist: pd.DataFrame, dfENUstat: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
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
    print('ind = {!s}'.format(ind))

    for axis, crd, color in zip(ax[:3], ('dUTM.E', 'dUTM.N', 'dEllH'), colors):
        axis.bar(ind, dfENUdist[crd], alpha=0.5, color=color, edgecolor='none')
        # rotate the ticks on this axis
        axis.set_xticklabels(dfENUdist.index.tolist(), rotation='vertical')

    width = .25
    for i, crd, color in zip((-1, 0, +1), ('dUTM.E', 'dUTM.N', 'dEllH'), colors):
        ax[-1].bar(ind - (i * width), dfENUdist[crd], width=width, alpha=0.5, color=color, edgecolor='none')
        # rotate the ticks on this axis
        ax[-1].set_xticklabels(dfENUdist.index.tolist(), rotation='vertical')

    # set the ticks on the x-axis
    ax[0].set_xlim([ind[0], ind[-1]])
    ax[0].xaxis.set_major_locator(FixedLocator(ind))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    return
