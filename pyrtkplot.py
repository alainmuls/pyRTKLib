#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
import pandas as pd
import numpy as np
import math
import utm as UTM
import pandas_profiling as pp

import am_config as amc
from ampyutils import utm, amutils
from rnx2rtkp import parse_rtk_files
from plot import plot_position, plot_scatter, plot_sats_column, plot_clock
from stats import enu_statistics as enu_stat

__author__ = 'amuls'


def treatCmdOpts(argv):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = amc.cBaseName + ' make plots from RTKLib processed files (position and/or residuals)'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-f', '--file', help='RTKLib processed position file', required=True, type=str)
    parser.add_argument('-d', '--dir', help='Root directory for RTKLib processed files (default .)', required=False, type=str, default='.')
    # parser.add_argument('-r', '--resFile', help='RTKLib residuals file', type=str, required=False, default=None)
    parser.add_argument('-m', '--marker', help='Geodetic coordinates (lat,lon,ellH) of reference point in degrees: 50.8440152778 4.3929283333 151.39179 for RMA, 50.93277777 4.46258333 123 for Peutie, default 0 0 0 means use mean position', nargs=3, type=str, required=False, default=["0", "0", "0"])

    parser.add_argument('-p', '--plots', help='displays interactive plots (default True)', action='store_true', required=False, default=False)
    parser.add_argument('-o', '--overwrite', help='overwrite intermediate files (default False)', action='store_true', required=False)
    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.file, args.dir, args.marker, args.plots, args.overwrite, args.logging


def main(argv):
    """
    pyRTKPlot adds UTM coordinates to output of rnx2rtkp.
    If 'stat' file is available, calculates xDOP values, and make plots of statictics

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # some options for diasplay of dataframes
    pd.set_option('display.max_columns', None)  # or 1000
    pd.set_option('display.max_rows', None)  # or 1000
    pd.set_option('display.max_colwidth', -1)  # or 199
    # limit float precision
    json.encoder.FLOAT_REPR = lambda o: format(o, '.3f')

    # treat command line options
    rtkPosFile, rtkDir, crdMarker, showPlots, overwrite, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger = amc.createLoggers(baseName=os.path.basename(__file__), dir=rtkDir, logLevels=logLevels)

    # change to selected directory if exists
    # print('rtkDir = %s' % rtkDir)
    if not os.path.exists(rtkDir):
        logger.error('{func:s}: directory {dir:s} does not exists'.format(func=cFuncName, dir=colored(rtkDir, 'red')))
        sys.exit(amc.E_DIR_NOT_EXIST)
    else:
        os.chdir(rtkDir)
        logger.info('{func:s}: changed to dir {dir:s}'.format(func=cFuncName, dir=colored(rtkDir, 'green')))

    # store information
    dInfo = {}
    dInfo['dir'] = rtkDir
    dInfo['rtkPosFile'] = rtkPosFile
    dInfo['rtkStatFile'] = dInfo['rtkPosFile'] + '.stat'
    dInfo['posn'] = dInfo['rtkPosFile'] + '.posn'
    dInfo['posnstat'] = dInfo['posn'] + '.html'
    amc.dRTK['info'] = dInfo

    # GNSS system is last part of root directory
    amc.dRTK['syst'] = 'UNKNOWN'
    for _, syst in enumerate(['GAL', 'GPS', 'COM']):
        if syst.lower() in amc.dRTK['info']['dir'].lower():
            amc.dRTK['syst'] = syst
    # print('amc.dRTK['syst'] = {:s}'.format(amc.dRTK['syst']))

    # info about PDOP bins and statistics
    dPDOP = {}
    dPDOP['bins'] = [0, 2, 3, 4, 5, 6, math.inf]
    amc.dRTK['PDOP'] = dPDOP

    # set the reference point
    dMarker = {}
    dMarker['lat'], dMarker['lon'], dMarker['ellH'] = map(float, crdMarker)
    print('crdMarker = {!s}'.format(crdMarker))

    if [dMarker['lat'], dMarker['lon'], dMarker['ellH']] == [0, 0, 0]:
        dMarker['lat'] = dMarker['lon'] = dMarker['ellH'] = np.NaN
        dMarker['UTM.E'] = dMarker['UTM.N'] = np.NaN
        dMarker['UTM.Z'] = dMarker['UTM.L'] = ''
    else:
        dMarker['UTM.E'], dMarker['UTM.N'], dMarker['UTM.Z'], dMarker['UTM.L'] = UTM.from_latlon(dMarker['lat'], dMarker['lon'])

    logger.info('{func:s}: marker coordinates = {crd!s}'.format(func=cFuncName, crd=dMarker))
    amc.dRTK['marker'] = dMarker

    # check wether pos and stat file are present, else exit
    if not os.access(os.path.join(rtkDir, amc.dRTK['info']['rtkPosFile']), os.R_OK) or not os.access(os.path.join(rtkDir, amc.dRTK['info']['rtkStatFile']), os.R_OK):
        logger.error('{func:s}: file {pos:s} or {stat:s} is not accessible'.format(func=cFuncName, pos=os.path.join(rtkDir, amc.dRTK['info']['rtkPosFile']), stat=os.path.join(rtkDir, amc.dRTK['info']['rtkStatFile'])))

        sys.exit(amc.E_FILE_NOT_EXIST)

    # read the position file into a dataframe and add dUTM coordinates
    logger.info('{func:s}: parsing RTKLib pos file {pos:s}'.format(pos=amc.dRTK['info']['rtkPosFile'], func=cFuncName))
    dfPosn = parse_rtk_files.parseRTKLibPositionFile(logger=logger)

    # calculate the weighted avergae of llh & enu
    amc.dRTK['WAvg'] = parse_rtk_files.weightedAverage(dfPos=dfPosn, logger=logger)

    # find difference with reference and ax/min limits for UTM plot
    logger.info('{func:s}: calculating coordinate difference with reference/mean position'.format(func=cFuncName))
    dfCrd, dCrdLim = plot_position.crdDiff(dMarker=amc.dRTK['marker'], dfUTMh=dfPosn[['UTM.E', 'UTM.N', 'ellH']], plotCrds=['UTM.E', 'UTM.N', 'ellH'], logger=logger)
    # merge dfCrd into dfPosn
    dfPosn[['dUTM.E', 'dUTM.N', 'dEllH']] = dfCrd[['UTM.E', 'UTM.N', 'ellH']]

    # work on the statistics file
    # split it in relavant parts
    dTmpFiles = parse_rtk_files.splitStatusFile(amc.dRTK['info']['rtkStatFile'], logger=logger)

    # parse the satellite file (contains Az, El, PRRes, CN0)
    dfSats = parse_rtk_files.parseSatelliteStatistics(dTmpFiles['sat'], logger=logger)
    dfSats.to_csv(amc.dRTK['info']['rtkPosFile'] + '.sats', index=None, header=True)
    logger.info('{func:s}: created csv file {csv:s}'.format(func=cFuncName, csv=colored(amc.dRTK['info']['rtkPosFile'] + '.sats', 'green')))

    # determine statistics of PR residuals
    amc.dRTK['PRres'] = parse_rtk_files.parseResiduals(dfSats, logger=logger)
    # calculate DOP values from El, Az info for each TOW
    dfDOPs = parse_rtk_files.calcDOPs(dfSats, logger=logger)
    dfDOPs.to_csv(amc.dRTK['info']['rtkPosFile'] + '.dops', index=None, header=True)
    logger.info('{func:s}: created csv file {csv:s}'.format(func=cFuncName, csv=colored(amc.dRTK['info']['rtkPosFile'] + '.dops', 'green')))

    # merge the PDOP column of dfDOPs into dfPosn and interpolate the PDOP column
    dfResults = pd.merge(left=dfPosn, right=dfDOPs[['DT', 'PDOP']], left_on='DT', right_on='DT', how='left')
    dfPosn = dfResults.interpolate()

    logger.info('{func:s}: amc.dRTK =\n{settings!s}'.format(func=cFuncName, settings=json.dumps(amc.dRTK, sort_keys=False, indent=4)))
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfPosn, dfName='dfPosn')

    dfPosn.to_csv(amc.dRTK['info']['posn'], index=None, header=True)
    logger.info('{func:s}: created csv file {csv:s}'.format(func=cFuncName, csv=colored(amc.dRTK['info']['rtkPosFile'] + '.posn', 'green')))

    # calculate per DOP bin the statistics of PDOP
    parse_rtk_files.addPDOPStatistics(dRtk=amc.dRTK, dfPos=dfPosn, logger=logger)

    # add statistics for the E,N,U coordinate differences
    enu_stat.enu_statistics(dRtk=amc.dRTK, dfENU=dfPosn[['DT', 'dUTM.E', 'dUTM.N', 'dEllH']], logger=logger)
    # add statistics for the E,N,U coordinate differences
    enu_stat.enu_distribution(dRtk=amc.dRTK, dfENU=dfPosn[['DT', 'dUTM.E', 'dUTM.N', 'dEllH', 'PDOP']], logger=logger)
    logger.info('{func:s}: dRTK =\n{settings!s}'.format(func=cFuncName, settings=json.dumps(amc.dRTK, sort_keys=False, indent=4)))

    # # store statistics for dfPosn
    # logger.info('{func:s}: creating pandas profile report {ppname:s} for dfPosn, {help:s}'.format(ppname=colored(amc.dRTK['info']['posnstat'], 'green'), help=colored('be patient', 'red'), func=cFuncName))
    # dfProfile = dfPosn[['DT', 'ns', 'dUTM.E', 'dUTM.N', 'dEllH', 'sdn', 'sde', 'sdu', 'PDOP']]

    # ppTitle = 'Report on {posn:s} - {syst:s} - {date:s}'.format(posn=amc.dRTK['info']['posn'], syst=amc.dRTK['syst'], date=amc.dRTK['Time']['date'])

    # profile = pp.ProfileReport(df=dfProfile, check_correlation_pearson=False, correlations={'pearson': False, 'spearman': False, 'kendall': False, 'phi_k': False, 'cramers': False, 'recoded': False}, title=ppTitle)
    # profile.to_file(output_file=amc.dRTK['info']['posnstat'])

    sys.exit(99)

    # parse the clock stats
    dfCLKs = parse_rtk_files.parseClockBias(dTmpFiles['clk'], logger=logger)
    dfCLKs.to_csv(amc.dRTK['info']['rtkPosFile'] + '.clks', index=None, header=True)
    logger.info('{func:s}: created csv file {csv:s}'.format(func=cFuncName, csv=colored(amc.dRTK['info']['rtkPosFile'] + '.clks', 'green')))

    # for debug
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfPosn, dfName='dfPosn')
    amc.logDataframeInfo(df=dfPosn, dfName='dfPosn', callerName=cFuncName, logger=logger)
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfSats, dfName='dfSats')
    amc.logDataframeInfo(df=dfSats, dfName='dfSats', callerName=cFuncName, logger=logger)
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfDOPs, dfName='dfDOPs')
    amc.logDataframeInfo(df=dfDOPs, dfName='dfDOPs', callerName=cFuncName, logger=logger)
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfCLKs, dfName='dfCLKs')
    amc.logDataframeInfo(df=dfCLKs, dfName='dfCLKs', callerName=cFuncName, logger=logger)
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfCrd, dfName='dfCrd')
    amc.logDataframeInfo(df=dfCrd, dfName='dfCrd', callerName=cFuncName, logger=logger)

    # create the position plot (use DOP to color segments)
    sys.exit(66)

    logger.info('{func:s}: creating Position coordinates plot'.format(func=cFuncName))
    plot_position.plotUTMOffset(dRtk=amc.dRTK, dfPos=dfPosn, dfCrd=dfCrd, dCrdLim=dCrdLim, logger=logger, showplot=showPlots)
    # create the UTM N-E scatter plot
    logger.info('{func:s}: creating position scatter plots'.format(func=cFuncName))
    plot_scatter.plotUTMScatter(dRtk=amc.dRTK, dfPos=dfPosn, dfCrd=dfCrd, dCrdLim=dCrdLim, logger=logger, showplot=showPlots)
    plot_scatter.plotUTMScatterBin(dRtk=amc.dRTK, dfPos=dfPosn, dfCrd=dfCrd, dCrdLim=dCrdLim, logger=logger, showplot=showPlots)

    # plot pseudo-range residus
    dPRResInfo = {'name': 'PRres', 'yrange': [-10, 7.5], 'title': 'PR Residuals', 'unit': 'm', 'linestyle': '-'}
    logger.info('{func:s}: creating dPRRes plots based on dict {dict!s}'.format(func=cFuncName, dict=dPRResInfo))
    plot_sats_column.plotRTKLibSatsColumn(dCol=dPRResInfo, dRtk=amc.dRTK, dfSVs=dfSats, logger=logger, showplot=showPlots)

    # plot CN0
    dCN0Info = {'name': 'CN0', 'yrange': [20, 60], 'title': 'CN0 Ratio', 'unit': 'dBHz', 'linestyle': '-'}
    logger.info('{func:s}: creating CN0 plots based on dict {dict!s}'.format(func=cFuncName, dict=dCN0Info))
    plot_sats_column.plotRTKLibSatsColumn(dCol=dCN0Info, dRtk=amc.dRTK, dfSVs=dfSats, logger=logger, showplot=showPlots)

    # # plot elevation
    dElevInfo = {'name': 'Elev', 'yrange': [0, 90], 'title': 'Elevation', 'unit': 'Deg', 'linestyle': '-'}
    logger.info('{func:s}: creating Elev plots based on dict {dict!s}'.format(func=cFuncName, dict=dElevInfo))
    plot_sats_column.plotRTKLibSatsColumn(dCol=dElevInfo, dRtk=amc.dRTK, dfSVs=dfSats, logger=logger, showplot=showPlots)

    # # plot the receiver clock
    logger.info('{func:s}: creating Clock plots'.format(func=cFuncName))
    plot_clock.plotClock(dfClk=dfCLKs, dRtk=amc.dRTK, logger=logger, showplot=showPlots)

    logger.info('{func:s}: final amc.dRTK =\n{settings!s}'.format(func=cFuncName, settings=json.dumps(amc.dRTK, sort_keys=False, indent=4)))

    jsonName = amc.dRTK['info']['rtkPosFile'] + '.json'
    with open(jsonName, 'w') as f:
        json.dump(amc.dRTK, f, ensure_ascii=False, indent=4)

    logger.info('{func:s}: created json file {json:s}'.format(func=cFuncName, json=colored(jsonName, 'green')))


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
