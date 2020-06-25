import matplotlib.pyplot as plt
from matplotlib import dates
import numpy as np
import os
import pandas as pd
import sys
from termcolor import colored
import logging
import am_config as amc

from plot import plot_utils
from ampyutils import amutils

__author__ = 'amuls'


def plotRTKLibSatsColumn(dCol: dict, dRtk: dict, dfSVs: pd.DataFrame, logger: logging.Logger, showplot: bool = False):
    """
    plotRTKLibSatsColumn plots a data columln from the stas dataframe
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # set up the plot
    plt.style.use('ggplot')

    # create a dataframe dfMerged with columns DT and the columns we want (PRres, CN0, Elev) selected by dCol
    # check for which GNSS we have data to display
    GNSSSysts = []
    if dRtk['PRres']['#GAL'] > 0:
        GNSSSysts.append('GAL')
    if dRtk['PRres']['#GPS'] > 0:
        GNSSSysts.append('GPS')
    if dRtk['PRres']['#GAL'] > 0 and dRtk['PRres']['#GPS'] > 0:
        GNSSSysts.append('COM')

    logger.info('{func:s}: processing GNSS Systems = {systs!s}'.format(func=cFuncName, systs=GNSSSysts))

    for _, GNSSSyst in enumerate(GNSSSysts):
        logger.info('{func:s}: working on GNSS = {syst:s}'.format(func=cFuncName, syst=GNSSSyst))

        # start with create a dataframe containing the DTs (unique values) and per column the value of column 'col'
        dfSatsCol = pd.DataFrame(dfSVs.DT.unique(), columns=['DT'])
        logger.debug('{func:s}: dfSatsCol.columns = {cols!s}'.format(func=cFuncName, cols=dfSatsCol.columns))
        # logger.debug('{func:s}: final dRtk =\n{settings!s}'.format(func=cFuncName, settings=json.dumps(dRtk, sort_keys=False, indent=4)))

        if GNSSSyst == 'COM':
            curSVsList = dRtk['PRres']['GALList'] + dRtk['PRres']['GPSList']
        else:
            curSVsList = dRtk['PRres']['%sList' % GNSSSyst]

        logger.debug('{func:s} #{line:d}: curSVsList of system {syst:s} = {list!s}   {count:d}'.format(func=cFuncName, list=curSVsList, count=len(curSVsList), syst=GNSSSyst, line=amc.lineno()))

        # add column to this dataframe for each SV and for its selected value 'col'
        for i, sv in enumerate(curSVsList):
            dfSVCol = pd.DataFrame(dfSVs[['DT', dCol['name']]][dfSVs['SV'] == sv])
            dfSVCol.rename(columns={dCol['name']: sv}, inplace=True)
            # logger.debug('{func:s}: dfSVCol = {df!s}  (#{size!s})'.format(df=dfSVCol, size=dfSVCol.size, func=cFuncName))

            # merge together
            dfMerged = pd.merge(dfSatsCol, dfSVCol, on=['DT'], how='outer')
            dfSatsCol = dfMerged

        # add a count of the number of residuals we have
        dfMerged['#{name:s}'.format(name=dCol['name'])] = dfMerged.apply(lambda x: x.count() - 1, axis=1)  # -1 else DT is counted as well

        amc.logDataframeInfo(df=dfMerged, dfName='dfMerged', callerName=cFuncName, logger=logger)

        # only processing dCol['name'] of current system, plot both vs DT and statistics
        if dCol['name'] == 'PRres':
            fig, axis = plt.subplots(nrows=4, ncols=1, figsize=(24.0, 20.0))
        elif dCol['name'] == 'CN0':
            fig, axis = plt.subplots(nrows=3, ncols=1, figsize=(24.0, 20.0))
        else:
            fig, axis = plt.subplots(nrows=2, ncols=1, figsize=(24.0, 16.0))

        # determine the discrete colors for SVs
        # colormap = plt.cm.nipy_spectral  # I suggest to use nipy_spectral, Set1, Paired
        # colors = [colormap(i) for i in np.linspace(0, 1, len(dfMerged.columns) - 1)]
        # print('colors = {!s}'.format(colors))
        # determine the discrete colors for all observables
        colormap = plt.cm.tab20  # I suggest to use nipy_spectral, Set1, Paired
        colors = [colormap(i) for i in np.linspace(0, 1, len(dfMerged.columns) - 1)]
        # print('colors = {!s}'.format(colors))

        # Plot first the dCol['name'] versus DT
        ax1 = axis[0]

        # color white background between [-2 and +2]
        if dCol['name'] == 'PRres':
            ax1.fill_between(dfMerged['DT'], -2, +2, color='lightgreen', alpha=0.2)

        # plot the selected 'col' values excluding last column
        dfMerged[dfMerged.columns[:-1]].set_index('DT').plot(ax=ax1, color=colors, marker='.', markersize=1, linestyle='', alpha=0.8)
        # name the ax1 and set limits
        ax1.set_ylabel('{title:s} [{unit:s}]'.format(title=dCol['title'], unit=dCol['unit']), fontsize='large')
        if not dCol['yrange'][0] is np.nan:
            ax1.set_ylim(dCol['yrange'])

        # title for plot
        ax1.set_title('{title:s} {syst:s} - {date:s}'.format(title=dCol['title'], syst=GNSSSyst, date=dRtk['Time']['date']), fontsize='x-large')

        # add legend
        # ax1.legend(bbox_to_anchor=(0.5, 0.025), loc='lower center', ncol=min(np.size(curSVsList), 15), fontsize='small', markerscale=10)

        # create the ticks for the time axis
        dtFormat = plot_utils.determine_datetime_ticks(startDT=dfMerged['DT'].iloc[0], endDT=dfMerged['DT'].iloc[-1])

        if dtFormat['minutes']:
            ax1.xaxis.set_major_locator(dates.MinuteLocator(byminute=[0, 15, 30, 45], interval=1))
        else:
            ax1.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every 4 hours
        ax1.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

        ax1.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
        ax1.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))

        ax1.xaxis.set_tick_params(rotation=0)
        for tick in ax1.xaxis.get_major_ticks():
            tick.label1.set_horizontalalignment('center')

        ax1.annotate(r'$\copyright$ Alain Muls (alain.muls@mil.be)', xy=(1, 1), xycoords='axes fraction', xytext=(0, 0), textcoords='offset pixels', horizontalalignment='right', verticalalignment='bottom', weight='strong', fontsize='large')

        # SECOND: PLOT THE STATISTICS FOR DCOL['NAME'] FOR ALL SVS
        logger.info('{func:s}: {gnss:s} statistics {name:s}\n{stat!s}'.format(func=cFuncName, name=dCol['name'], gnss=GNSSSyst, stat=dfMerged.describe()))

        ax2 = axis[1]
        # plotTitle = '{title:s} {gnss:s} statistics - {date:s}'.format(title=dCol['title'], gnss=GNSSSyst, date=dRtk['Time']['date'])

        # leave out the column DT and the count column (eg '#PRres')
        selectCols = [x for x in dfMerged.columns if x not in ['DT', '#{name:s}'.format(name=dCol['name'])]]
        # print('selectCols = {!s}'.format(selectCols))
        boxPlot = dfMerged[selectCols].plot(ax=ax2, kind='box', legend=True, fontsize='large', colormap='jet', return_type='dict', ylim=dCol['yrange'], rot=90, notch=True, patch_artist=True)
        # name the ax1 and set limits
        ax2.set_ylabel('%s [%s]' % (dCol['title'], dCol['unit']), fontsize='large')
        if not dCol['yrange'][0] is np.nan:
            ax2.set_ylim(dCol['yrange'])

        # beautify the boxplots
        svColors = []
        if GNSSSyst == 'GAL' or GNSSSyst == 'GPS':
            # for i, color in enumerate(colors):
            svColors = colors
        else:
            for _, SV in enumerate(curSVsList):
                if SV.startswith('E'):
                    svColors.append('blue')
                else:
                    svColors.append('red')

        for item in ['boxes', 'fliers', 'medians']:  # , 'whiskers', 'fliers', 'medians', 'caps']:
            for patch, color in zip(boxPlot[item], svColors):
                patch.set(color=color, linewidth=2)
                if item in ['boxes', 'fliers']:
                    # make transparent background fill
                    patch.set_alpha(0.15)

        # double the colors because whiskers exist at both sides
        doubleSVColors = []
        for i, svColor in enumerate(svColors):
            doubleSVColors.append(svColor)
            doubleSVColors.append(svColor)

        # color elements that are twice available
        for item in ['whiskers', 'caps']:  # , 'whiskers', 'fliers', 'medians', 'caps']:
            for patch, color in zip(boxPlot[item], doubleSVColors):
                patch.set(color=color, linewidth=2)

        # THIRD: FOR CN0 WE ALSO PLOT THE TIMEWISE DIFFERENCE
        dfMergedDiff = pd.DataFrame()
        if dCol['name'] == 'CN0':
            dfMergedDiff = dfMerged[dfMerged.columns[1:]].diff()
            dfMergedDiff = dfMergedDiff.mask(dfMergedDiff.abs() <= 1)
            dfMergedDiff.insert(loc=0, column='DT', value=dfMerged['DT'])
            dfMergedDiff.dropna(axis=0, how='all', subset=dfMerged.columns[1:], inplace=True)
            dfMergedDiff.dropna(axis=1, how='all', inplace=True)

            logger.debug('{func:s}: SVs observed (CN0 value) dfMerged.columns = {cols!s}'.format(func=cFuncName, cols=dfMerged.columns))
            logger.debug('{func:s}: SVs with SN0 diff > 1 dfMergedDiff.columns = {cols!s}'.format(func=cFuncName, cols=dfMergedDiff.columns))

            # THIRD: create the CN0 difference plot on the 3rd axis
            ax3 = axis[2]
            ax3.set_xlim([dfMerged['DT'].iat[0], dfMerged['DT'].iat[-1]])

            # plot the selected 'col' values
            for sv in dfMergedDiff.columns[1:-1]:
                logger.debug('{func:s}: {syst:s} {sv:s}'.format(func=cFuncName, syst=GNSSSyst, sv=sv))
                svcolor = svColors[curSVsList.index(sv)]
                # print('sv = {!s}   {!s}'.format(sv, svcolor))
                markerline, stemlines, baseline = ax3.stem(dfMergedDiff['DT'], dfMergedDiff[sv], label=sv)
                plt.setp(stemlines, color=svcolor, linewidth=2)
                plt.setp(markerline, color=svcolor, markersize=4)

            ax3.set_ylabel('Diff %s [%s]' % (dCol['title'], dCol['unit']), fontsize='large')

            # create the ticks for the time axis
            dtFormat = plot_utils.determine_datetime_ticks(startDT=dfMerged['DT'].iloc[0], endDT=dfMerged['DT'].iloc[-1])

            if dtFormat['minutes']:
                ax3.xaxis.set_major_locator(dates.MinuteLocator(byminute=[0, 15, 30, 45], interval=1))
            else:
                ax3.xaxis.set_major_locator(dates.HourLocator(interval=dtFormat['hourInterval']))   # every 4 hours
            ax3.xaxis.set_major_formatter(dates.DateFormatter('%H:%M'))  # hours and minutes

            ax3.xaxis.set_minor_locator(dates.DayLocator(interval=1))    # every day
            ax3.xaxis.set_minor_formatter(dates.DateFormatter('\n%d-%m-%Y'))

            ax3.xaxis.set_tick_params(rotation=0)
            for tick in ax3.xaxis.get_major_ticks():
                tick.label1.set_horizontalalignment('center')

        elif dCol['name'] == 'PRres':
            # THIRD: FOR PRRES WE ALSO PLOT THE PERCENTAGE OF PRRES WITHIN [-2, +2]
            ax3 = axis[2]
            ax4 = axis[3]

            # get the list of SVs for this GNSS
            if GNSSSyst == 'COM':
                curSVsList = dRtk['PRres']['GALList'] + dRtk['PRres']['GPSList']
            else:
                curSVsList = dRtk['PRres']['%sList' % GNSSSyst]

            logger.debug('{func:s} #{line:d}: curSVsList = {list!s}   {count:d}'.format(func=cFuncName, list=curSVsList, count=len(curSVsList), line=amc.lineno()))

            # create a dataframe indexed by SVID and which holds the #PR, #PRreslt2, %PRreslt2
            dfSVPR = pd.DataFrame(curSVsList, columns=['SV']).set_index('SV', drop=False)
            # add dummy columns for holding the residu info
            dfSVPR = dfSVPR.reindex(columns=['SV', '#res', '#reslt2', '#pcreslt2'])

            if GNSSSyst == 'COM':
                curSVsPRRes = {k: v for d in (dRtk['PRres']['GALSVs'], dRtk['PRres']['GPSSVs']) for k, v in d.items()}
            else:
                curSVsPRRes = dRtk['PRres']['%sSVs' % GNSSSyst]

            logger.debug('{func:s} #{line:d}: curSVsPRRes = {list!s}   {count:d}'.format(func=cFuncName, list=curSVsPRRes, count=len(curSVsPRRes), line=amc.lineno()))

            for i, sv in enumerate(curSVsList):
                dfSVPR.loc[dfSVPR['SV'] == sv, '#res'] = curSVsPRRes[sv]['count']
                dfSVPR.loc[dfSVPR['SV'] == sv, '#reslt2'] = curSVsPRRes[sv]['PRlt2']
                dfSVPR.loc[dfSVPR['SV'] == sv, '#pcreslt2'] = curSVsPRRes[sv]['PRlt2%']

            amc.logDataframeInfo(df=dfSVPR, dfName='dfSVPR', callerName=cFuncName, logger=logger)

            # plot the bars for PRres and PRReslt2
            dfSVPR.plot(kind='bar', ax=ax3, x='SV', y=['#res', '#reslt2'], edgecolor='white', fontsize='large', alpha=0.5)
            ax3.legend(labels=[r'#PRres', r'#PRres $\leq$ 2'], fontsize='medium')

            start, end = ax3.get_xlim()
            # print('start = {!s}'.format(start))
            # print('end = {!s}'.format(end))
            # ax3.set_xlim(left=start-1, right=end+1)

            # beatify the boxplot
            svRects = []
            for i, rect in enumerate(ax3.patches):
                # print('i = {:d}  rect = {!s}'.format(i, rect))
                if i < len(curSVsList):
                    svRects.append(rect)

            # for i, rect in enumerate(ax3.patches):
            #     # print('i = {:d}  len = {:d}'.format(i, len(curSVsList)))
            #     if i % 2:  # 2 bars per SV
            #         # get_width pulls left or right; get_y pushes up or down
            #         sv = curSVsList[int(i / 2)]
            #         # print('SV = {:s}  rect = {!s}'.format(sv, rect))
            #         svRect = svRects[int(i / 2)]
            #         ax3.text(svRect.get_x() + svRect.get_width(), svRect.get_y() + svRect.get_height(), '{:.2f}%'.format(dfSVPR.loc[sv]['#pcreslt2']), fontsize='medium', color='green', horizontalalignment='center')

            # name the y axis
            ax3.set_ylabel('# of {:s}'.format(dCol['name']), fontsize='large')

            # plot representing the percentage
            dfSVPR.plot(kind='bar', ax=ax4, x='SV', y='#pcreslt2', fontsize='large', sharex=ax3, color=svColors, alpha=0.5)

            ax4.legend(labels=[r'%PRres $\leq$ 2'], fontsize='medium')
            ax4.set_ylim([50, 101])
            ax4.tick_params(axis='y')

            # name the y axis
            ax4.set_ylabel(r'% $\in$ [-2, +2]'.format(dCol['name']), fontsize='large')

            # color the ticks on ax4 axis
            for xtick, color in zip(ax4.get_xticklabels(), svColors):
                xtick.set_color(color)

            # set percantage in the bars
            bars = ax4.patches
            print('bars = {!s}'.format(bars))
            # Text on the top of each barplot
            for i, bar in enumerate(bars):
                ax4.text(x=bar.get_x() + bar.get_width() / 2, y=bar.get_y() + 52, s='{rnd:.1f}'.format(rnd=bar.get_height()), rotation=90, fontsize=8, color='black', verticalalignment='bottom')

    # save the plot in subdir png of GNSSSystem
    amutils.mkdir_p(os.path.join(dRtk['info']['dir'], 'png'))
    pngName = os.path.join(dRtk['info']['dir'], 'png', os.path.splitext(dRtk['info']['rtkPosFile'])[0] + '-{col:s}.png'.format(col=dCol['name']))
    fig.savefig(pngName, dpi=fig.dpi)

    logger.info('{func:s}: created plot {plot:s}'.format(func=cFuncName, plot=colored(pngName, 'green')))

    if showplot:
        plt.show(block=True)
    else:
        plt.close(fig)
