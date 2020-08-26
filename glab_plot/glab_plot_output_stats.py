import matplotlib.pyplot as plt
from termcolor import colored
import sys
import logging
import os
import pandas as pd

import am_config as amc
from glab import glab_constants as glc
from ampyutils import amutils

__author__ = 'amuls'


def plot_glab_statistics(df_dopenu: pd.DataFrame, scale: float, logger: logging.Logger, showplot: bool = False):
    """
    plot_glab_statistics plots the position statitictics according to COP bins
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: plotting position statistics'.format(func=cFuncName))

    # set up the plot
    plt.style.use('ggplot')

    # get info for the plot titles
    plot_title, proc_options, rx_geod = amc.get_title_info(logger=logger)

    # subplots
    fig, axes = plt.subplots(nrows=1, ncols=len(amc.dRTK['dop_bins']) - 1, sharey=True, figsize=(10.0, 5.0))
    fig.subplots_adjust(wspace=0.1)

    fig.suptitle('{title:s}'.format(title=plot_title), **glc.title_font)

    # plot annotations
    axes[0].annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    axes[-1].annotate(proc_options, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # copyright this
    axes[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -50), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')

    amutils.printHeadTailDataFrame(df=df_dopenu, name='OUTPUT section of df_dopenu', index=False)

    # go over all PDOP bins and plot according to the markersBin defined
    print(amc.dRTK['dop_bins'][:-1])
    print(amc.dRTK['dop_bins'][1:])

    for dop_min, dop_max, ax in zip(amc.dRTK['dop_bins'][:-1], amc.dRTK['dop_bins'][1:], axes):
        bin_interval = 'bin{:d}-{:.0f}'.format(dop_min, dop_max)
        logger.info('{func:s}: bin = {bin!s}'.format(bin=bin_interval, func=cFuncName))

        index_bin = (df_dopenu['PDOP'] > dop_min) & (df_dopenu['PDOP'] <= dop_max)

        amutils.printHeadTailDataFrame(df=df_dopenu[index_bin], name='OUTPUT section of df_dopenu', index=False)

        # create box-plot for coordinate differences of ENU
        df_dopenu[index_bin].boxplot(column=['dN0', 'dE0', 'dU0'], ax=ax)

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    sys.exit(5)
