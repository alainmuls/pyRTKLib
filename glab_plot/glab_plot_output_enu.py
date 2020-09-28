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


def plot_glab_position(dfCrd: pd.DataFrame, scale: float, logger: logging.Logger, showplot: bool = False):
    """
    plot_glab_position plots the position difference wrt to Nominal a priori position
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: plotting position offset'.format(func=cFuncName))

    # set up the plot
    plt.style.use('ggplot')

    # get info for the plot titles
    plot_title, proc_options, rx_geod = amc.get_title_info(logger=logger)

    # subplots
    fig, ax = plt.subplots(nrows=4, ncols=1, sharex=True, figsize=(16.0, 12.0))

    fig.suptitle('{title:s}'.format(title=plot_title), **glc.title_font)

    # plot annotations
    ax[0].annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    ax[0].annotate(proc_options, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # copyright this
    ax[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -50), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')

    # plot the ENU difference xwrt nominal initial position and display the standard deviation, xDOP
    for i, (crd, sdCrd) in enumerate(zip(glc.dgLab['OUTPUT']['dENU'], glc.dgLab['OUTPUT']['sdENU'])):
        # select the axis to use for this coordinate
        axis = ax[i]

        # get the statistics for this coordinate
        crd_stats = amc.dRTK['dgLABng']['stats']['crd'][crd]

        # color for markers and alpha colors for error bars
        rgb = mpcolors.colorConverter.to_rgb(glc.enu_colors[i])
        rgb_error = amutils.make_rgb_transparent(rgb, (1, 1, 1), 0.4)

        # plot coordinate differences and error bars
        axis.errorbar(x=dfCrd['DT'].values, y=dfCrd[crd], yerr=dfCrd[sdCrd], linestyle='none', fmt='.', ecolor=rgb_error, capthick=1, markersize=1, color=glc.enu_colors[i])

        # set dimensions of y-axis (double for UP scale)
        if crd == 'dU0':
            axis.set_ylim([crd_stats['wavg'] - scale * 2, crd_stats['wavg'] + scale * 2])
        else:
            axis.set_ylim([crd_stats['wavg'] - scale, crd_stats['wavg'] + scale])

        axis.set_ylabel('{crd:s} [m]'.format(crd=crd, fontsize='large'), color=glc.enu_colors[i], weight='ultrabold')

        # annotate each subplot with its reference position
        stat_str = '\n'.join((
                             r'gLab={:.3f} ($\pm${:.3f})'.format(crd_stats['kf'], crd_stats['sdkf']),
                             r'',
                             r'WAvg={:.3f} ($\pm${:.3f})'.format(crd_stats['wavg'], crd_stats['sdwavg']),
                             r'',
                             r'Range=[{:.2f}..{:.2f}]'.format(crd_stats['max'], crd_stats['min'])
                             ))
        # place a text box in upper left in axes coords
        axis.text(1.01, 0.95, stat_str, transform=axis.transAxes, fontsize='small', verticalalignment='top', color=glc.enu_colors[i], weight='strong')

        # annotatetxt = markerAnnotation(crd, sdCrd)
        # axis.annotate(annotatetxt, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='large')

        # title of sub-plot
        # axis.set_title('{crd:s} offset'.format(crd=str.capitalize(crd), fontsize='large'))
        axis.set_xlabel('')

    # last subplot: number of satellites & PDOP
    # plot #SVs on left axis
    axis = ax[-1]
    axis.set_ylim([0, 24])
    axis.set_ylabel('#SVs [-]', fontsize='large', color='grey', weight='ultrabold')
    # axis.set_xlabel('Time [sec]', fontsize='large')

    # plot the number of SVs and color as function of the GNSSs used
    for (i_gnss, gnss, gnss_color) in zip([1, 1, 2], ['GAL', 'GPS', ''], ['blue', 'red', 'grey']):
        if i_gnss == 2:
            axis.fill_between(dfCrd['DT'].values, 0, dfCrd['#SVs'], where=(dfCrd['#GNSSs'] == i_gnss), alpha=0.25, linestyle='-', linewidth=2, color=gnss_color, interpolate=False)
        else:
            axis.fill_between(dfCrd['DT'].values, 0, dfCrd['#SVs'], where=((dfCrd['#GNSSs'] == i_gnss) & (gnss == dfCrd['GNSSs'])), alpha=0.25, linestyle='-', linewidth=2, color=gnss_color, interpolate=False)

    # plot PDOP on second y-axis
    axis_right = axis.twinx()

    axis_right.set_ylim([0, 10])
    axis_right.set_ylabel('PDOP [-]', fontsize='large', color='darkorchid', weight='ultrabold')

    # plot PDOP value
    axis_right.plot(dfCrd['DT'], dfCrd['PDOP'], linestyle='', marker='.', markersize=1, color='darkorchid', label='PDOP')

    # set limits for the x-axis
    axis.set_xlim([dfCrd['DT'].iloc[0], dfCrd['DT'].iloc[-1]])

    # create the ticks for the time axis
    dtFormat = plot_utils.determine_datetime_ticks(startDT=dfCrd['DT'].iloc[0], endDT=dfCrd['DT'].iloc[-1])
    if dtFormat['minutes']:
        axis.xaxis.set_major_locator(dates.MinuteLocator(byminute=range(10, 60, 10), interval=1))
    else:
        axis.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every

    axis.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
    axis.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))
    axis.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

    axis.xaxis.set_tick_params(rotation=0)
    for tick in axis.xaxis.get_major_ticks():
        tick.label1.set_horizontalalignment('center')

    # save the plot in subdir png of GNSSSystem
    dir_png = os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'], 'png')
    png_filename = os.path.join(dir_png, '{out:s}-ENU.png'.format(out=amc.dRTK['glab_out'].replace('.', '-')))
    amutils.mkdir_p(dir_png)
    fig.savefig(png_filename, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(png_filename, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    return


def plot_glab_scatter(dfCrd: pd.DataFrame, scale: float, center: str, logger: logging.Logger, showplot: bool = False):
    """
    plot_glab_scatter plots the horizontal position difference wrt to Nominal a priori position
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    logger.info('{func:s}: plotting EN scattering'.format(func=cFuncName))

    # set up the plot
    plt.style.use('ggplot')

    # get info for the plot titles
    plot_title, proc_options, rx_geod = amc.get_title_info(logger=logger)

    # subplots
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(11.0, 11.0))

    # figure title
    fig.suptitle('{title:s}'.format(title=plot_title, **glc.title_font))

    # plot annotations
    ax.annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    ax.annotate(proc_options, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # copyright this
    ax.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -50), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')

    # annotate with reference position
    txt_rx_posn = r'$\varphi = ${lat:.8f}, $\lambda = ${lon:.8f}'.format(lat=rx_geod[0], lon=rx_geod[1])

    ax.annotate(txt_rx_posn, xy=(0, 0), xycoords='axes fraction', xytext=(0, -45), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='strong', fontsize='medium')

    # draw circles for distancd evaluation on plot
    if center == 'origin':
        wavg_E = wavg_N = 0
    else:
        wavg_E = amc.dRTK['dgLABng']['stats']['crd']['dE0']['wavg']
        wavg_N = amc.dRTK['dgLABng']['stats']['crd']['dN0']['wavg']
    circle_center = (wavg_E, wavg_N)

    for radius in np.linspace(scale / 5, scale * 2, num=10):
        newCircle = plt.Circle(circle_center, radius, color='blue', fill=False, clip_on=True, alpha=0.4)
        ax.add_artist(newCircle)
        # annotate the radius for 1, 2, 5 and 10 meter
        # if radius in [1, 2, 3, 4, 5, 10]:
        # ax.annotate('{radius:.2f}m'.format(radius=radius), xy=(np.pi / 4, radius), xytext=(np.pi / 4, radius), textcoords='polar', xycoords='polar', clip_on=True, color='blue', alpha=0.4)
        ax.annotate('{radius:.2f}m'.format(radius=radius), xy=(wavg_E + np.cos(np.pi / 4) * radius, wavg_N + np.sin(np.pi / 4) * radius), xytext=(wavg_E + np.cos(np.pi / 4) * radius, wavg_N + np.sin(np.pi / 4) * radius), clip_on=True, color='blue', alpha=0.4)

    # get the marker styles
    markerBins = glc.predefined_marker_styles()

    # go over all PDOP bins and plot according to the markersBin defined
    for i in range(len(glc.dop_bins) - 1, 0, -1):
        binInterval = 'bin{:d}-{:.0f}'.format(glc.dop_bins[i - 1], glc.dop_bins[i])
        logger.debug('{func:s}: binInterval = {bin!s}'.format(bin=binInterval, func=cFuncName))

        index4Bin = (dfCrd['PDOP'] > glc.dop_bins[i - 1]) & (dfCrd['PDOP'] <= glc.dop_bins[i])

        # get th epercentage of observations within this dop_bin
        bin_percentage = '{perc:.1f}'.format(perc=amc.dRTK['dgLABng']['stats']['dop_bin'][binInterval]['perc'] * 100)
        ax.plot(dfCrd.loc[index4Bin, 'dE0'], dfCrd.loc[index4Bin, 'dN0'], label=r'{!s} $\leq$ PDOP $<$ {!s} ({:s}%)'.format(glc.dop_bins[i - 1], glc.dop_bins[i], bin_percentage), **markerBins[i - 1])

        # print('i = {:d} color = {!s}'.format(i, markerBins[i]['color']))

    # lcoation of legend
    ax.legend(loc='best', markerscale=6, fontsize='x-small')

    # add titles to axes
    ax.set_xlim([wavg_E - scale, wavg_E + scale])
    ax.set_ylim([wavg_N - scale, wavg_N + scale])
    ax.set_aspect(aspect='equal', adjustable='box')

    # nema the axis
    ax.set_xlabel('East [m]', fontsize='large')
    ax.set_ylabel('North [m]', fontsize='large')

    # save the plot in subdir png of GNSSSystem
    dir_png = os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'], 'png')
    png_filename = os.path.join(dir_png, '{out:s}-scatter.png'.format(out=amc.dRTK['glab_out'].replace('.', '-')))
    amutils.mkdir_p(dir_png)
    fig.savefig(png_filename, dpi=fig.dpi)

    logger.info('{func:s}: created scatter plot {plot:s}'.format(func=cFuncName, plot=colored(png_filename, 'green')))

    if showplot:
        plt.show(block=False)
    else:
        plt.close(fig)


def plot_glab_scatter_bin(dfCrd: pd.DataFrame, scale: float, center: str, logger: logging.Logger, showplot: bool = False):
    """
    plot_glab_scatter plots the horizontal position difference wrt to Nominal a priori position
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    logger.info('{func:s}: plotting EN scattering'.format(func=cFuncName))

    # # select colors for E, N, U coordinate difference
    # colors = []
    # colors.append([51 / 256., 204 / 256., 51 / 256.])

    # set up the plot
    plt.style.use('ggplot')

    # get info for the plot titles
    plot_title, proc_options, rx_geod = amc.get_title_info(logger=logger)

    # subplots
    fig, ax = plt.subplots(nrows=2, ncols=3, figsize=(16.0, 11.0))

    # figure title
    fig.suptitle('{title:s}'.format(title=plot_title), **glc.title_font)

    # plot annotations
    ax[0][0].annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    ax[0][2].annotate(proc_options, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # copyright this
    ax[1][2].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -70), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')

    # annotate with reference position
    txt_rx_posn = r'$\varphi = ${lat:.8f}, $\lambda = ${lon:.8f}'.format(lat=rx_geod[0], lon=rx_geod[1])

    ax[1][0].annotate(txt_rx_posn, xy=(0, 0), xycoords='axes fraction', xytext=(0, -70), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='strong', fontsize='medium')

    # get the marker styles
    markerBins = glc.predefined_marker_styles()

    # go over all PDOP bins and plot according to the markersBin defined
    for i in range(0, len(glc.dop_bins) - 1):
        binInterval = 'bin{:d}-{:.0f}'.format(glc.dop_bins[i], glc.dop_bins[i + 1])
        logger.info('{func:s}: binInterval = {bin!s}'.format(bin=binInterval, func=cFuncName))

        index4Bin = (dfCrd['PDOP'] > glc.dop_bins[i]) & (dfCrd['PDOP'] <= glc.dop_bins[i + 1])

        # get the axis
        axis = ax[i // 3][i % 3]

        # get th epercentage of observations within this dop_bin
        bin_percentage = '{perc:.1f}'.format(perc=amc.dRTK['dgLABng']['stats']['dop_bin'][binInterval]['perc'] * 100)
        lblBin = r'{!s} $\leq$ PDOP $<$ {!s} ({:s}%, #{:d})'.format(glc.dop_bins[i], glc.dop_bins[i + 1], bin_percentage, amc.dRTK['dgLABng']['stats']['dop_bin'][binInterval]['count'])
        logger.info('{func:s}: {bin:s}'.format(func=cFuncName, bin=lblBin))

        # define center position
        if center == 'origin':
            wavg_E = wavg_N = 0
        else:
            wavg_E = amc.dRTK['dgLABng']['stats']['crd']['dE0']['wavg']
            wavg_N = amc.dRTK['dgLABng']['stats']['crd']['dN0']['wavg']
        circle_center = (wavg_E, wavg_N)

        # draw circles for distancd evaluation on plot
        for radius in np.linspace(scale / 5, scale * 2, num=10):
            newCircle = plt.Circle(circle_center, radius, color='blue', fill=False, clip_on=True, alpha=0.4)
            axis.add_artist(newCircle)
            # annotate the radius for 1, 2, 5 and 10 meter
            # if radius in [1, 2, 3, 4, 5, 10]:
            # axis.annotate('{radius:.2f}m'.format(radius=radius), xy=(np.pi / 4, radius), xytext=(np.pi / 4, radius), textcoords='polar', xycoords='polar', clip_on=True, color='blue', alpha=0.4)
            axis.annotate('{radius:.2f}m'.format(radius=radius), xy=(wavg_E + np.cos(np.pi / 4) * radius, wavg_N + np.sin(np.pi / 4) * radius), xytext=(wavg_E + np.cos(np.pi / 4) * radius, wavg_N + np.sin(np.pi / 4) * radius), clip_on=True, color='blue', alpha=0.4)

        # plot the coordinates for each bin
        axis.plot(dfCrd.loc[index4Bin, 'dE0'], dfCrd.loc[index4Bin, 'dN0'], label=r'{!s} $\leq$ PDOP $<$ {!s} ({:s}%)'.format(glc.dop_bins[i], glc.dop_bins[i + 1], bin_percentage), **markerBins[(i)])

        # lcoation of legend
        axis.legend(loc='best', markerscale=6, fontsize='x-small')

        # add titles to axes
        axis.set_xlim([wavg_E - scale, wavg_E + scale])
        axis.set_ylim([wavg_N - scale, wavg_N + scale])
        axis.set_aspect(aspect='equal', adjustable='box')

        # nema the axis
        if i > 2:
            axis.set_xlabel('East [m]', fontsize='large')
            axis.set_ylabel('North [m]', fontsize='large')

    # save the plot in subdir png of GNSSSystem
    dir_png = os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'], 'png')
    png_filename = os.path.join(dir_png, '{out:s}-scatter-bins.png'.format(out=amc.dRTK['glab_out'].replace('.', '-')))
    amutils.mkdir_p(dir_png)
    fig.savefig(png_filename, dpi=fig.dpi)

    logger.info('{func:s}: created scatter plot {plot:s}'.format(func=cFuncName, plot=colored(png_filename, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)


def plot_glab_xdop(dfCrd: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_xdop plot the DOP values vs time
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')
    logger.info('{func:s}: plotting xDOP'.format(func=cFuncName))

    # set up the plot
    plt.style.use('ggplot')

    # get info for the plot titles
    plot_title, proc_options, rx_geod = amc.get_title_info(logger=logger)

    # subplots
    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(12.0, 8.0))

    # figure title
    fig.suptitle('{title:s}'.format(title=plot_title), **glc.title_font)

    # plot annotations
    ax.annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    ax.annotate(proc_options, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # copyright this
    ax.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -50), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')

    # plot the xDOP values vs time
    for (xdop, dop_color) in zip(dfCrd[glc.dgLab['OUTPUT']['XDOP']], glc.dop_colors):
        if xdop == 'PDOP':
            ax.fill_between(x=dfCrd['DT'], y1=0, y2=dfCrd[xdop], color=dop_color, linestyle='-', linewidth=0, interpolate=False, alpha=0.15)
        ax.plot(dfCrd['DT'], dfCrd[xdop], color=dop_color, linestyle='', marker='.', markersize=1, label=xdop)

    # lcoation of legend
    ax.legend(loc='best', markerscale=6, fontsize='x-small')

    # add titles to axes
    ax.set_ylim([0, 10])

    # name the axis
    ax.set_ylabel('DOP [-]', fontsize='large')

    # set limits for the x-axis
    ax.set_xlim([dfCrd['DT'].iloc[0], dfCrd['DT'].iloc[-1]])

    # create the ticks for the time axis
    dtFormat = plot_utils.determine_datetime_ticks(startDT=dfCrd['DT'].iloc[0], endDT=dfCrd['DT'].iloc[-1])
    if not dtFormat['minutes']:
        #     # ax.xaxis.set_major_locator(dates.MinuteLocator(byminute=range(10, 60, 10), interval=1))
        #     pass
        # else:
        ax.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every

    ax.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
    ax.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))
    ax.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

    ax.xaxis.set_tick_params(rotation=0)
    for tick in ax.xaxis.get_major_ticks():
        tick.label1.set_horizontalalignment('center')

    # save the plot in subdir png of GNSSSystem
    dir_png = os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'], 'png')
    png_filename = os.path.join(dir_png, '{out:s}-DOP.png'.format(out=amc.dRTK['glab_out'].replace('.', '-')))
    amutils.mkdir_p(dir_png)
    fig.savefig(png_filename, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(png_filename, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)
