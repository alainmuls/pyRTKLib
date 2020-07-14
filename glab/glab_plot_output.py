import matplotlib.pyplot as plt
from matplotlib import colors as mpcolors
from termcolor import colored
import os
import pandas as pd
import sys
import logging
from datetime import datetime
from typing import Tuple
from matplotlib import dates

from ampyutils import amutils
import am_config as amc
from plot import plot_utils
from glab import glab_constants as glc

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def get_title_info(logger: logging.Logger) -> Tuple[str, str]:
    """
    get_title_info gets basic info from the gLab['INFO'] dict for the plot
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: get information for reporting on plot'.format(func=cFuncName))

    # make title for plot
    date = datetime.strptime(amc.dRTK['INFO']['epoch_first'][:10], '%d/%m/%Y')
    time_first = datetime.strptime(amc.dRTK['INFO']['epoch_first'][11:19], '%H:%M:%S')
    time_last = datetime.strptime(amc.dRTK['INFO']['epoch_last'][11:19], '%H:%M:%S')
    gnss_used = amc.dRTK['INFO']['gnss_used']
    gnss_meas = amc.dRTK['INFO']['meas']
    obs_file = os.path.basename(amc.dRTK['INFO']['obs'])
    nav_file = os.path.basename(amc.dRTK['INFO']['nav'])

    return date, time_first, time_last, gnss_used, gnss_meas, obs_file, nav_file


def plot_glab_position(dfCrd: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plot_glab_position plots the position difference wrt to Nominal a priori position
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: plotting position offset'.format(func=cFuncName))

    # select colors for E, N, U coordinate difference
    colors = []
    colors.append([51 / 256., 204 / 256., 51 / 256.])
    colors.append([51 / 256., 51 / 256., 255 / 256.])
    colors.append([255 / 256., 51 / 256., 51 / 256.])

    # set up the plot
    plt.style.use('ggplot')

    # get info for the plot titles
    obs_date, start_time, end_time, GNSSs, GNSS_meas, obs_name, nav_name = get_title_info(logger=logger)

    # subplots
    fig, ax = plt.subplots(nrows=4, ncols=1, sharex=True, figsize=(16.0, 12.0))
    fig.suptitle('{posf:s} - {obs_date:s}'.format(posf=obs_name, obs_date='{date:s} ({first:s}-{last:s})'.format(date=obs_date.strftime('%d/%m/%Y'), first=start_time.strftime('%H:%M:%S'), last=end_time.strftime('%H:%M:%S'))), weight='ultrabold', fontsize='x-large')

    # plot annotations
    ax[0].annotate('{conf:s}'.format(conf=amc.dRTK['glab_out']), xy=(0, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='left', verticalalignment='bottom', weight='ultrabold', fontsize='small')
    txt_filter = 'Iono {iono:s} - Tropo {tropo:s} - RefClk {clk:s} - mask {mask:s}'.format(iono=amc.dRTK['INFO']['iono'], tropo=amc.dRTK['INFO']['tropo'], clk=amc.dRTK['INFO']['ref_clk'], mask=amc.dRTK['INFO']['mask'])
    ax[0].annotate('{syst:s}\n{meas:s}\n{filter:s}'.format(syst=GNSSs, meas=GNSS_meas, filter=txt_filter), xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='small')

    # copyright this
    ax[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 0), xycoords='axes fraction', xytext=(0, -50), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='ultrabold', fontsize='x-small')

    # get mean/stddev values of the columns glc.dgLab['OUTPUT']['dENU']
    crd_mean = {}
    crd_std = {}
    for crd in glc.dgLab['OUTPUT']['dENU']:
        # get max/min for this crd and the previous ones
        crd_mean[crd] = dfCrd[crd].quantile(q=0.5, interpolation='linear')
        crd_std[crd] = dfCrd[crd].std()

    # plot the ENU difference xwrt nominal initial position and display the standard deviation, xDOP
    for i, (crd, sdCrd) in enumerate(zip(glc.dgLab['OUTPUT']['dENU'], glc.dgLab['OUTPUT']['sdENU'])):
        # select the axis to use for this coordinate
        axis = ax[i]

        # color for markers and alpha colors for error bars
        rgb = mpcolors.colorConverter.to_rgb(colors[i])
        rgb_error = amutils.make_rgb_transparent(rgb, (1, 1, 1), 0.4)

        # plot coordinate differences and error bars
        axis.errorbar(x=dfCrd['DT'].values, y=dfCrd[crd], yerr=dfCrd[sdCrd], linestyle='none', fmt='.', ecolor=rgb_error, capthick=1, markersize=1, color=colors[i])

        # set dimensions of y-axis
        if crd == 'dU0':
            axis.set_ylim([crd_mean[crd] - 10, crd_mean[crd] + 10])
        else:
            axis.set_ylim([crd_mean[crd] - 5, crd_mean[crd] + 5])

        axis.set_ylabel('{crd:s} [m]'.format(crd=crd, fontsize='large'), color=colors[i], weight='ultrabold')

        # annotate each subplot with its reference position
        textstr = '\n'.join((
                            r'$\mu={:.2f}$'.format(crd_mean[crd]),
                            r'$\sigma={:.2f}$'.format(crd_std[crd])))
        # place a text box in upper left in axes coords
        axis.text(1.01, 0.95, textstr, transform=axis.transAxes, fontsize='small', verticalalignment='top', color=colors[i], weight='strong')

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

    # plot the number of SVs and color as function of the number of GNSSs used
    for i_gnss in range(1, dfCrd['#GNSSs'].max() + 1):
        axis.fill_between(dfCrd['DT'].values, 0, dfCrd['#SVs'], where=(dfCrd['#GNSSs'] == i_gnss), alpha=0.4, linestyle='-', linewidth=1, color=colors[i_gnss], label='#SVs', interpolate=False)

    # plot PDOP on second y-axis
    axis_right = axis.twinx()

    axis_right.set_ylim([0, 10])
    axis_right.set_ylabel('PDOP [-]', fontsize='large', color='darkorchid', weight='ultrabold')

    # plot PDOP value
    axis_right.plot(dfCrd['DT'], dfCrd['PDOP'], linestyle='', marker='.', markersize=1, color='darkorchid', label='PDOP')

    # create the ticks for the time axis
    dtFormat = plot_utils.determine_datetime_ticks(startDT=dfCrd['DT'].iloc[0], endDT=dfCrd['DT'].iloc[-1])
    if dtFormat['minutes']:
        # axis.xaxis.set_major_locator(dates.MinuteLocator(byminute=range(10, 60, 10), interval=1))
        pass
    else:
        axis.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every

    axis.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
    axis.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))
    axis.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

    axis.xaxis.set_tick_params(rotation=0)
    for tick in axis.xaxis.get_major_ticks():
        tick.label1.set_horizontalalignment('center')

    # save the plot in subdir png of GNSSSystem
    amutils.mkdir_p(os.path.join(amc.dRTK['dir_root'], 'png'))
    pngName = os.path.join(amc.dRTK['dir_root'], 'png', '{obs:s}-ENU.png'.format(obs=obs_name.replace('.', '-')))
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    return
