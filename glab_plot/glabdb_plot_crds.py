import matplotlib.pyplot as plt
from matplotlib import colors as mpcolors
from termcolor import colored
import os
import pandas as pd
import sys
import logging
from matplotlib import dates
import numpy as np

from ampyutils import amutils
import am_config as amc
from plot import plot_utils
from glab import glab_constants as glc

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plot_glabdb_position(crds: list, prcodes: list, df_crds: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_glabdb_position plots the crds for all prcodes
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: plotting coordinates per pr-code'.format(func=cFuncName))

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig, ax = plt.subplots(nrows=len(crds), ncols=1, sharex=True, figsize=(16.0, 9.0))

    title_txt = 'daily coordinates comparison {yyyy:4d}/{start:03d} - {yyyy:4d}/{end:03d}'.format(start=amc.dRTK['options']['doy_begin'], end=amc.dRTK['options']['doy_last'], yyyy=amc.dRTK['options']['yyyy'])
    fig.suptitle(title_txt, **glc.title_font)

    # plot annotations
    # ax[0].annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # ax[0].annotate(proc_options, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # copyright this
    ax[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -50), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')


    # go over the crds
    for i, crd in enumerate(glc.dgLab['OUTPUT'][crds]):
        axis = ax[i]
        # color for markers and alpha colors for error bars
        rgb = mpcolors.colorConverter.to_rgb(glc.enu_colors[i])
        rgb_error = amutils.make_rgb_transparent(rgb, (1, 1, 1), 0.4)

        # go over the prcodes
        for prcode in prcodes:
            logger.info('{func:s}: plotting for combination {crd:s} - {prcode:s}'.format(crd=crd, prcode=prcode, func=cFuncName))

            # select rows for prcode and for crd
            df_crd_prcode = df_crds[(df_crds['prcodes'].str.contains(prcode)) & (df_crds['crds'] == crd)]
            amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_crd_prcode, dfName='df_crd_prcode'.format(crds=crds))

            # plot coordinate differences and error bars
            axis.errorbar(x=df_crd_prcode['DT'].values, y=df_crd_prcode['mean'], yerr=df_crd_prcode['std'], linestyle='none', fmt='.', ecolor=rgb_error, capthick=1, markersize=1, color=glc.enu_colors[i])

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    return
