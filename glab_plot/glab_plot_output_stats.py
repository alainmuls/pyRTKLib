import matplotlib.pyplot as plt
from matplotlib.ticker import AutoLocator, AutoMinorLocator
from termcolor import colored
import sys
import logging
import os
import pandas as pd
import seaborn as sns

import am_config as amc
from glab import glab_constants as glc
from ampyutils import amutils

__author__ = 'amuls'


def plot_glab_statistics2(df_dopenu: pd.DataFrame, scale: float, logger: logging.Logger, showplot: bool = False):
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
    for dop_min, dop_max in zip(amc.dRTK['dop_bins'][:-1], amc.dRTK['dop_bins'][1:]):
        bin_interval = 'bin{:d}-{:.0f}'.format(dop_min, dop_max)
        logger.info('{func:s}: setting for PDOP bin = {bin!s}'.format(bin=bin_interval, func=cFuncName))

        # add column 'bin' for grouping the results during plotting
        df_dopenu.loc[(df_dopenu['PDOP'] > dop_min) & (df_dopenu['PDOP'] <= dop_max), 'bin'] = bin_interval

    # creating the boxplot array for the coordinate differences:
    bp_dict = df_dopenu[['dN0', 'dE0', 'dU0', 'bin']].boxplot(by='bin', layout=(3, 1), figsize=(10, 8), return_type='both', patch_artist=True)

    # # get the statistics for this coordinate
    # for crd in ['dN0', 'dE0', 'dU0']:
    #     crd_stats = amc.dRTK['dgLABng']['stats']['crd'][crd]

    # adjusting the Axes instances to your needs
    for i, (row_key, (ax, row)), dCrd in zip([0, 1, 2], bp_dict.items(), ['dN0', 'dE0', 'dU0']):
        # removing shared axes:
        grouper = ax.get_shared_y_axes()
        shared_ys = [a for a in grouper]
        for ax_list in shared_ys:
            for ax2 in ax_list:
                grouper.remove(ax2)

        # adjusting tick positions:
        ax.yaxis.set_major_locator(AutoLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())

        # create the labels on Y-axis
        # set dimensions of y-axis (double for UP scale)
        ax.set_ylim([-1.5 * scale, 1.5 * scale])
        ax.set_ylabel('{crd:s} [m]'.format(crd=dCrd, fontsize='large'), color=glc.enu_colors[i], weight='ultrabold')
        ax.set_ylabel(dCrd)
        # making tick labels visible:
        plt.setp(ax.get_yticklabels(), visible=True)

        for j, box in enumerate(row['boxes']):
            box.set_facecolor(glc.dop_colors[j])

        # annotate the plot
        if i == 0:
            ax.annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')

            ax.annotate(proc_options, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')
        elif i == 2:
            # copyright this
            ax.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -50), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')

        ax.set_title('')  # remove subplot title
        ax.set_xlabel('')  # remove x label

    plt.suptitle('{title:s}'.format(title=plot_title), **glc.title_font)

    fig_bh, axarr = plt.subplots(2, 1, figsize=(12, 8))

    # plot boxplot
    bp_dict = df_dopenu[['dN0', 'dE0', 'dU0', 'bin']].boxplot(by='bin', layout=(3, 1), figsize=(10, 8), return_type='both', patch_artist=True, ax=axarr[0])
    axarr[0] = bp_dict['dE0'].ax

    print('bp_dict[dE0] = {!s}'.format(bp_dict['dE0'].ax))
    print('type(bp_dict[dE0]) = {!s}'.format(type(bp_dict['dE0'])))

    # plot histogram
    kwargs = dict(alpha=0.5, bins=100, density=True, stacked=True)
    axes_hist = df_dopenu[['dN0', 'dE0', 'dU0']].hist(by=df_dopenu.bin, grid=True, figsize=(12, 5), layout=(1, 6), sharex=True, sharey=True, **kwargs, color=glc.enu_colors, ax=axarr[1])
    axarr[1] = axes_hist

    print('axes_hist = {!s}'.format(axes_hist))

    # save the plot in subdir png of GNSSSystem
    dir_png = os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'], 'png')
    png_filename = os.path.join(dir_png, '{out:s}-DOP-stats.png'.format(out=amc.dRTK['glab_out'].replace('.', '-')))
    amutils.mkdir_p(dir_png)
    plt.savefig(png_filename)

    if showplot:
        plt.show(block=True)
    else:
        plt.close()

    sys.exit(5)


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
    for dop_min, dop_max in zip(amc.dRTK['dop_bins'][:-1], amc.dRTK['dop_bins'][1:]):
        bin_interval = 'bin{:d}-{:.0f}'.format(dop_min, dop_max)
        dop_bins.append(bin_interval)
        logger.info('{func:s}: setting for PDOP bin = {bin!s}'.format(bin=bin_interval, func=cFuncName))

        # add column 'bin' for grouping the results during plotting
        df_dopenu.loc[(df_dopenu['PDOP'] > dop_min) & (df_dopenu['PDOP'] <= dop_max), 'bin'] = bin_interval

    amutils.printHeadTailDataFrame(df=df_dopenu, name='df_dopenu', index=False)

    fig, axes = plt.subplots(nrows=6, ncols=len(dop_bins), sharex=True, gridspec_kw={"height_ratios": (.15, .85, .15, .85, .15, .85)})

    print('axes = {!s}'.format(axes))
    print('type(axes) = {!s}'.format(type(axes)))

    ax_box = axes[0::2]
    print('ax_box = {!s}'.format(ax_box))
    ax_hist = axes[1::2]
    print('ax_hist = {!s}'.format(ax_hist))

    # go over the coordinate differences
    for i, crd in enumerate(['dN0', 'dE0', 'dU0']):
        # create the plot holding for each DOP bin the histogram and bixplot combined in a subfigure
        print('-' * 25)
        print(i)

        # plot the statistics per DOP bin
        for j, bin in enumerate(dop_bins):

            sns.boxplot(df_dopenu.loc[df_dopenu['bin'] == bin][crd], ax=ax_box[i][j])
            sns.distplot(df_dopenu.loc[df_dopenu['bin'] == bin][crd], ax=ax_hist[i][j])

        # sns.boxplot(df_dopenu.loc[df_dopenu['bin'] == 'bin2-3'][crd], ax=ax_box[i][1])
        # sns.distplot(df_dopenu.loc[df_dopenu['bin'] == 'bin2-3'][crd], ax=ax_hist[i][1])

    plt.show()
