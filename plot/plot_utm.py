import matplotlib.pyplot as plt
from matplotlib import dates
from matplotlib import colors as mpcolors
from termcolor import colored
import os
import pandas as pd
import sys
import logging

from ampyutils import amutils
from plot import plot_utils
from rnx2rtkp import rtklibconstants as rtkc
import am_config as amc

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plot_utm_ellh(dRtk: dict, dfUTM: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
     plots the UTM coordinates

    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # select colors for position mode
    # colors = []
    # colors.append([51 / 256., 204 / 256., 51 / 256.])
    # colors.append([51 / 256., 51 / 256., 255 / 256.])
    # colors.append([255 / 256., 51 / 256., 51 / 256.])
    colors = ['tab:white', 'tab:green', 'tab:olive', 'tab:orange', 'tab:cyan', 'tab:blue', 'tab:red', 'tab:pink', 'tab:purple', 'tab:brown']

    # what to plot
    crds2Plot = ['UTM.E', 'UTM.N', 'ellH', 'age']
    stdDev2Plot = ['sde', 'sdn', 'sdu']
    stdDevWAvg = ['sdUTM.E', 'sdUTM.N', 'sdellH']

    # set up the plot
    plt.style.use('ggplot')

    # subplots
    fig, ax = plt.subplots(nrows=len(crds2Plot), ncols=1, sharex=True, figsize=(20.0, 16.0))

    # make title for plot
    ax[0].annotate('{camp:s} - {date:s} - {marker:s} ({pos:s}, quality {mode:s})'.format(camp=dRtk['campaign'], date=dRtk['obsStart'].strftime('%d %b %Y'), marker=dRtk['marker'], pos=dRtk['posFile'], mode=dRtk['rtkqual'].upper()), xy=(0.5, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='center', verticalalignment='bottom', weight='strong', fontsize='large')

    # copyright this
    ax[-1].annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='large')

    # determine the difference to weighted average or marker position of UTM (N,E), ellH to plot
    dfCrd = pd.DataFrame(columns=crds2Plot[:3])
    originCrds = [float(amc.dRTK['WAVG'][crd]) for crd in crds2Plot[:3]]
    dfCrd = dfUTM[crds2Plot[:3]].sub(originCrds, axis='columns')
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfCrd, dfName='dfCrd')

    crdMax = max(dfCrd.max())
    crdMin = min(dfCrd.min())
    crdMax = int(crdMax + (1 if crdMax > 0 else -1))
    crdMin = int(crdMin + (1 if crdMin > 0 else -1))

    # plot the coordinates dN, dE, dU and ns
    for i, crd in enumerate(crds2Plot):
        if i < 3:  # subplots for coordinates display dN, dE, dU
            # plot over the different coordinate offsets using different colors

            # we plot offset to the weighted averga value
            # ax[i].plot(dfUTM['DT'], dCrd[crd], linestyle='', marker='.', markersize=2, color=colors[i], label=crd)
            # ax[i].fill_between(dfUTM['DT'], dCrd[crd]-dfUTM[stdDev2Plot[i]], dCrd[crd]+dfUTM[stdDev2Plot[i]], color=colors[i], alpha=0.15, interpolate=False)

            for key, value in rtkc.dRTKQual.items():
                # get the indices according to the position mode
                idx = dfUTM.index[dfUTM['Q'] == key]
                rgb = mpcolors.colorConverter.to_rgb(colors[key])
                rgb_new = amutils.make_rgb_transparent(rgb, (1, 1, 1), 0.3)

                # plot according to the color list if the length of the index is not 0
                if len(idx) > 0:
                    ax[i].errorbar(x=dfUTM.loc[idx]['DT'], y=dfCrd.loc[idx][crd], yerr=dfUTM.loc[idx][stdDev2Plot[i]], linestyle='None', fmt='o', ecolor=rgb_new, capthick=2, markersize=2, color=colors[key], label=value)

            # set dimensions of y-axis
            ax[i].set_ylim([crdMin, crdMax])
            ax[i].set_ylabel('{crd:s} [m]'.format(crd=crd, fontsize='large'))

            # lcoation of legend
            ax[i].legend(loc='best', markerscale=4)

            # annotate plot
            annotatetxt = r'WAvg: {crd:.3f}m $\pm$ {sdcrd:.3f}m'.format(crd=amc.dRTK['WAVG'][crds2Plot[i]], sdcrd=amc.dRTK['WAVG'][stdDevWAvg[i]])
            ax[i].annotate(annotatetxt, xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', fontweight='bold', fontsize='large')

        else:  # last subplot: age of corrections & #SVs
            # plot #SVs on left axis
            # ax[i].set_ylim([0, 24])

            # plot AGE value
            ax[i].set_ylabel('Age [s]', fontsize='large', color='darkorchid')
            ax[i].set_xlabel('Time [sec]', fontsize='large')
            ax[i].plot(dfUTM['DT'], dfUTM['age'], linestyle='', marker='x', markersize=2, color='darkorchid', label='age')
            ax[i].set_title('#SVs & Age of correction', fontsize='large', fontweight='bold')

            # plot number of SV on second y-axis
            axRight = ax[i].twinx()

            axRight.set_ylim([0, 25])
            axRight.set_ylabel('#SVs [-]', fontsize='large', color='grey')

            ax[i].fill_between(dfUTM['DT'], 0, dfUTM['ns'], alpha=0.5, linestyle='-', linewidth=3, color='grey', label='#SVs', interpolate=False)

            # create the ticks for the time axis
            dtFormat = plot_utils.determine_datetime_ticks(startDT=dfUTM['DT'].iloc[0], endDT=dfUTM['DT'].iloc[-1])

            if dtFormat['minutes']:
                if dfUTM.shape[0] > 300:
                    ax[i].xaxis.set_major_locator(dates.MinuteLocator(byminute=range(1, 60, 10), interval=1))
                else:
                    ax[i].xaxis.set_major_locator(dates.MinuteLocator(byminute=range(1, 60), interval=1))

            else:
                ax[i].xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every 4 hours
            ax[i].xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

            ax[i].xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
            ax[i].xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))

            ax[i].xaxis.set_tick_params(rotation=0)
            for tick in ax[i].xaxis.get_major_ticks():
                # tick.tick1line.set_markersize(0)
                # tick.tick2line.set_markersize(0)
                tick.label1.set_horizontalalignment('center')

    # save the plot in subdir png of GNSSSystem
    pngName = os.path.join(dRtk['posDir'], '{name:s}-ENU.png'.format(name=os.path.splitext(dRtk['posFile'])[0]))
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)

    return
