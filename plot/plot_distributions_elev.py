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


def plot_elev_distribution(dRtk: dict, df: pd.DataFrame, ds:pd.Series, obs_name: str, logger: logging.Logger, showplot: bool = False):
    """
    plot_elev_distribution plots the distribution of CN0 or PRres as function of elevation bins
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: creating {obs:s} distribution plot'.format(obs=obs_name, func=cFuncName))

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df, dfName=obs_name)

    # set up the plot
    plt.style.use('ggplot')

    # possible GNSS systems in df
    gnss_names = ('GAL', 'GPS')
    colors = ('blue', 'red')
    dgnss_avail = {}
    col_width = 0.25

    for gnss_name in gnss_names:
        dgnss_avail[gnss_name] = any([True for col in df  if col.startswith(gnss_name)])

    nrCols = 3
    col_move = 0
    if all(dgnss_avail.values()):
        tmpValue = divmod(len(df.columns) / 2, nrCols)
        col_move = 0.125
    else:
        tmpValue = divmod(len(df.columns), nrCols)

    syst_names = ' + '.join([k for k, v in dgnss_avail.items() if v == True])

    if (tmpValue[1] == 0):
        nrRows = int(tmpValue[0])
    else:
        nrRows = int(tmpValue[0]) + 1

    # get the elevation bins used
    elev_bins = list(set([col[3:] for col in df.columns]))
    elev_bins.sort()
    logger.info('{func:s}: elevation bins {bins!s}'.format(bins=elev_bins, func=cFuncName))
    logger.info('{func:s}: elevation bins sorted {bins!s}'.format(bins=elev_bins.sort(), func=cFuncName))

    fig, ax = plt.subplots(nrows=nrRows, ncols=nrCols, sharex=True, sharey=True, figsize=(20.0, 12.0))
    fig.suptitle('{syst:s} - {posf:s} - {date:s}: {obs:s} Statistics'.format(posf=dRtk['info']['rtkPosFile'], syst=syst_names, date=dRtk['Time']['date'], obs=obs_name), fontsize='xx-large')

    for i, elev_bin, gnss, color in zip((-1, +1), elev_bins, dgnss_avail, colors):

        # plot if the gnss is avaiable
        if dgnss_avail[gnss]:
            logger.info('{func:s}: plotting for system {gnss:s}'.format(gnss=gnss, func=cFuncName))

            # the indexes on the x-axis
            ind = np.arange(len(df.index))
            logger.info('{func:s}: ind = {ind!s}'.format(ind=ind, func=cFuncName))

            # columns of this system
            gnss_cols = ['{gnss:s}{bin:s}'.format(gnss=gnss, bin=elev_bin) for elev_bin in elev_bins]

            # calculate the total number of observations per system
            obs_per_bin = df.loc[:, gnss_cols].sum()
            logger.info('{func:s}: obs_per_bin = {nrobs!s}'.format(nrobs=obs_per_bin, func=cFuncName))

            if obs_name == 'PRres':
                # get index numbers for PRres between -2 and +2
                tmpValue = divmod(df.shape[0], 2)
                if tmpValue[1] == 0:
                    mid_prres = tmpValue[0] - 0.5
                else:
                    mid_prres = tmpValue

            for axis, col in zip(ax.flat, gnss_cols):
                # create a filled area for domain [-1, 1] if PRres plot
                if obs_name == 'PRres':
                    axis.axvspan(mid_prres - 2, mid_prres + 2, alpha=0.1, color='green')

                # draw a bar plot
                axis.bar(ind + (i * col_move), df[col] / obs_per_bin.sum() * 100, alpha=0.5, color=color, edgecolor='none')

                # rotate the ticks on this axis
                idx = np.asarray([i for i in range(len(df.index))])
                axis.set_xticks(idx)
                axis.set_xticklabels(df.index.tolist(), rotation='vertical')

                axis.annotate('#{:.0f} ({:.2f}%)'.format(ds[col], ds[col] / ds.sum() * 100), xy=(1, 1), xycoords='axes fraction', xytext=(0, -25), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='large')

                # set the title for sub-plot
                axis.set_title(label='Elevation bin {bin:s}'.format(bin=col[3:]), fontsize='x-large')

                # set the title for the Y axis
                axis.set_ylabel('{obs:s} statistics in [%]'.format(obs=obs_name))

    # save the plot in subdir png of GNSSSystem
    amutils.mkdir_p(os.path.join(dRtk['info']['dir'], 'png'))
    pngName = os.path.join(dRtk['info']['dir'], 'png', os.path.splitext(dRtk['info']['rtkPosFile'])[0] + '-{syst:s}-{obs:s}-dist.png'.format(syst=syst_names.replace(" ", ""), obs=obs_name))
    fig.savefig(pngName, dpi=fig.dpi)

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)
