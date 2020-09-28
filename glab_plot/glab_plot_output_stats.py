import matplotlib.pyplot as plt
from termcolor import colored
import sys
import logging
import os
import pandas as pd
import seaborn as sns

from ampyutils import amutils
import am_config as amc
from glab import glab_constants as glc
# from ampyutils import amutils

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

    # create additional column assigning the values of crd diffs to the correct PDOP bin
    dop_bins = []
    for dop_min, dop_max in zip(glc.dop_bins[:-1], glc.dop_bins[1:]):
        bin_interval = 'bin{:d}-{:.0f}'.format(dop_min, dop_max)
        dop_bins.append(bin_interval)
        logger.info('{func:s}: setting for PDOP bin = {bin!s}'.format(bin=bin_interval, func=cFuncName))

        # add column 'bin' for grouping the results during plotting
        df_dopenu.loc[(df_dopenu['PDOP'] > dop_min) & (df_dopenu['PDOP'] <= dop_max), 'bin'] = bin_interval

    # amutils.printHeadTailDataFrame(df=df_dopenu, name='df_dopenu', index=False)

    fig, axes = plt.subplots(nrows=4, ncols=len(dop_bins), sharex=True, sharey='row', figsize=(18, 8), gridspec_kw={'height_ratios': (.065, .065, .065, .805), 'wspace': 0.02, 'hspace': 0.02})

    # define the axis used for the boxplots and histogram
    ax_box = axes[:3]
    ax_hist = axes[-1]
    for axis in ax_hist:
        axis.set_xlim([-1.5 * scale, +1.5 * scale])
    # dist_bins = int(12 * scale)  # 4 bins per meter ???

    # go over the coordinate differences
    for i, (crd, enu_color) in enumerate(zip(glc.dgLab['OUTPUT']['dENU'], glc.enu_colors)):
        # create the plot holding for each DOP bin the histogram and bixplot combined in a subfigure
        for j, bin in enumerate(dop_bins):
            # boxplot in above 3xj subplots
            sns.boxplot(df_dopenu.loc[df_dopenu['bin'] == bin][crd], ax=ax_box[i][j], orient='h', color=enu_color, width=0.9, linewidth=1)
            cur_xaxis = ax_box[i][j].axes.get_xaxis()
            cur_xaxis.set_visible(False)
            # cur_yaxis = ax_box[i][j].axes.get_yaxis()
            if j == 0:
                ax_box[i][j].set_ylabel(crd, color=enu_color)
            else:
                cur_yaxis = ax_box[i][j].axes.get_yaxis()
                cur_yaxis.set_visible(False)

            # distplot in last subplot for column j
            sns.distplot(df_dopenu.loc[df_dopenu['bin'] == bin][crd], ax=ax_hist[j], color=glc.enu_colors[i])
            ax_hist[j].set_xlabel('PDOP[{bin:s}]'.format(bin=bin[3:]))

    # global title
    fig.suptitle('{title:s}'.format(title=plot_title), **glc.title_font)

    # plot annotations
    ax_box[0][0].annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    ax_box[0][-1].annotate(proc_options, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # copyright this
    ax_hist[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -70), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')

    # save the plot in subdir png of GNSSSystem
    dir_png = os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'], 'png')
    png_filename = os.path.join(dir_png, '{out:s}-boxhist.png'.format(out=amc.dRTK['glab_out'].replace('.', '-')))
    amutils.mkdir_p(dir_png)
    fig.savefig(png_filename, dpi=fig.dpi)

    logger.info('{func:s}: created statistics plot {plot:s}'.format(func=cFuncName, plot=colored(png_filename, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)
