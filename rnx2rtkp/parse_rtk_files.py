import pandas as pd
from termcolor import colored
import sys
import numpy as np
import os
import logging
import utm
import tempfile
from typing import Tuple

from ampyutils import amutils
from GNSS import gpstime
from rnx2rtkp import rtklibconstants as rtkc
import am_config as amc

__author__ = 'amuls'


def parseRTKLibPositionFile(logger: logging.Logger) -> pd.DataFrame:
    """
    parse the position file from RTKLIB processing into a dataframe
    """
    # set current function name
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: parsing RTKLib position file {posf:s}'.format(func=cFuncName, posf=amc.dRTK['info']['rtkPosFile']))

    # check whether the datafile is readable
    endHeaderLine = amutils.line_num_for_phrase_in_file('%  GPST', amc.dRTK['info']['rtkPosFile'])
    dfPos = pd.read_csv(amc.dRTK['info']['rtkPosFile'], header=endHeaderLine, delim_whitespace=True)
    dfPos = dfPos.rename(columns={'%': 'WNC', 'GPST': 'TOW', 'latitude(deg)': 'lat', 'longitude(deg)': 'lon', 'height(m)': 'ellH', 'sdn(m)': 'sdn', 'sde(m)': 'sde', 'sdu(m)': 'sdu', 'sdne(m)': 'sdne', 'sdeu(m)': 'sdeu', 'sdun(m)': 'sdun', 'age(s)': 'age'})

    # convert the GPS time to UTC
    dfPos['DT'] = dfPos.apply(lambda x: gpstime.UTCFromWT(x['WNC'], x['TOW']), axis=1)

    dTime = {}
    dTime['epochs'] = dfPos.shape[0]
    dTime['date'] = dfPos.DT.iloc[0].strftime('%d %b %Y')
    dTime['start'] = dfPos.DT.iloc[0].strftime('%H:%M:%S')
    dTime['end'] = dfPos.DT.iloc[-1].strftime('%H:%M:%S')
    amc.dRTK['Time'] = dTime

    # add UTM coordinates
    dfPos['UTM.E'], dfPos['UTM.N'], dfPos['UTM.Z'], dfPos['UTM.L'] = utm.from_latlon(dfPos['lat'].to_numpy(), dfPos['lon'].to_numpy())
    logger.info('{func:s}: added UTM coordiantes'.format(func=cFuncName))

    # inform user
    amc.logDataframeInfo(df=dfPos, dfName='dfPos', callerName=cFuncName, logger=logger)
    logger.info('{func:s}: dTime = {time!s}'.format(func=cFuncName, time=dTime))
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfPos, dfName='{posf:s}'.format(posf=amc.dRTK['info']['rtkPosFile']))

    # put the info of the dfPosn into debug logging
    logger.debug('{func:s}: dfPos info\n{info!s}'.format(info=dfPos.info(), func=cFuncName))

    return dfPos


def splitStatusFile(statFileName: str, logger: logging.Logger) -> dict:
    """
    splitStatusFile splits the statistics file into the POS, SAT, CLK & VELACC parts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.debug('{func:s}: splitting the statistics file {statf:s} into the POS, SAT, CLK & VELACC parts'.format(func=cFuncName, statf=statFileName))

    # read in the stats file and split it in the parts we need
    statParts = ('cart', 'sat', 'clk', 'vel')
    lineParts = ('$POS', '$SAT', '$CLK', '$VELACC')

    dStat = {}

    for statPart, linePart in zip(statParts, lineParts):
        dStat[statPart] = tempfile.NamedTemporaryFile(prefix='{:s}_'.format(statFileName), suffix='_{:s}'.format(statPart), delete=True)

        with open(dStat[statPart].name, 'w') as fTmp:
            fTmp.writelines(line for line in open(statFileName) if linePart in line)
            logger.info('{func:s}: size of {part:s} status file = {size:d}'.format(size=fTmp.tell(), part=statPart, func=cFuncName))
            # reset at start of file
            fTmp.seek(0)

    return dStat


def weightedAverage(dfPos: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    calculates the weighted average of LLH and ENU
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating weighted averages'.format(func=cFuncName))

    llh = ['lat', 'lon', 'ellH']
    UTMcrd = ['UTM.N', 'UTM.E', 'ellH']
    # dUTMcrd = ['dUTM.N', 'dUTM.E', 'dEllH']
    sdENU = ['sdn', 'sde', 'sdu']

    dWAVG = {}
    for values in zip(llh, sdENU):
        dWAVG[values[0]] = wavg(dfPos, values[0], values[1])
    for values in zip(UTMcrd, sdENU):
        dWAVG[values[0]] = wavg(dfPos, values[0], values[1])
    # for values in zip(dUTMcrd, sdENU):
    #     dWAVG[values[0]] = wavg(dfPos, values[0], values[1])
    for values in zip(sdENU, sdENU):
        dWAVG[values[0]] = wavg(dfPos, values[0], values[1])

    logger.info('{func:s}: weighted averages are {wavg!s}'.format(func=cFuncName, wavg=dWAVG))

    return dWAVG


def wavg(group: dict, avg_name: str, weight_name: str) -> float:
    """ http://stackoverflow.com/questions/10951341/pandas-dataframe-aggregate-function-using-multiple-columns
    In rare instance, we may not have weights, so just return the mean. Customize this if your business case
    should return otherwise.
    """
    coordinate = group[avg_name]
    invVariance = 1 / np.square(group[weight_name])

    try:
        return (coordinate * invVariance).sum() / invVariance.sum()
    except ZeroDivisionError:
        return coordinate.mean()


def parseSatelliteStatistics(statsSat: tempfile._TemporaryFileWrapper, logger: logging.Logger) -> pd.DataFrame:
    """
    parseSatelliteStatistics reads the SAT statitics file into a dataframe
    """
    # set current function name
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Parsing RTKLib satellites file {file:s} ({info:s})'.format(func=cFuncName, file=statsSat.name, info=colored('be patient', 'red')))

    dfSat = pd.read_csv(statsSat.name, header=None, sep=',', usecols=[*range(1, 11)])
    dfSat.columns = rtkc.dRTKPosStat['Res']['useCols']
    amutils.printHeadTailDataFrame(df=dfSat, name='dfSat range')

    # dfSat = pd.read_csv(statsSat.name, header=None, sep=',', names=rtkc.dRTKPosStat['Res']['colNames'], usecols=rtkc.dRTKPosStat['Res']['useCols'])
    # amutils.printHeadTailDataFrame(df=dfSat, name='dfSat usecol')

    # sys.exit(77)

    # add DT column
    dfSat['DT'] = dfSat.apply(lambda x: gpstime.UTCFromWT(x['WNC'], x['TOW']), axis=1)

    # if PRres == 0.0 => than I suppose only 4 SVs used, so no residuals can be calculated, so change to NaN
    dfSat.PRres.replace(0.0, np.nan, inplace=True)

    amc.logDataframeInfo(df=dfSat, dfName='dfSat', callerName=cFuncName, logger=logger)

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfSat, dfName='dfSat')

    return dfSat


def parse_sv_residuals(dfSat: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    parse_sv_residuals parses the observed resiudals of the satellites
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: parses observed resiudals of satellites'.format(func=cFuncName))

    # determine the list of satellites observed
    obsSVs = np.sort(dfSat.SV.unique())

    logger.info('{func:s}: observed SVs (#{nrsats:02d}):\n{sats!s}'.format(func=cFuncName, nrsats=len(obsSVs), sats=obsSVs))

    # determine statistics for each SV
    dSVList = {}
    dSVList['#total'] = len(obsSVs)
    nrGAL = 0
    nrGPS = 0
    GALList = []
    GPSList = []
    dGALsv = {}
    dGPSsv = {}

    for i, sv in enumerate(obsSVs):
        # do some statistics on this sv
        dSV = {}
        dSV['count'] = int(dfSat.PRres[dfSat['SV'] == sv].count())
        dSV['PRmean'] = dfSat.PRres[dfSat['SV'] == sv].mean()
        dSV['PRmedian'] = dfSat.PRres[dfSat['SV'] == sv].median()
        dSV['PRstd'] = dfSat.PRres[dfSat['SV'] == sv].std()
        s = dfSat.PRres[dfSat['SV'] == sv].between(-2, +2, inclusive=True)
        dSV['PRlt2'] = int(s.sum())
        if dSV['count']:
            dSV['PRlt2%'] = dSV['PRlt2'] / dSV['count'] * 100
        else:
            dSV['PRlt2%'] = 0

        if sv.startswith('E'):
            nrGAL += 1
            GALList.append(sv)
            dGALsv[sv] = dSV
        elif sv.startswith('G'):
            nrGPS += 1
            GPSList.append(sv)
            dGPSsv[sv] = dSV
        else:
            logger.error('{func:s}: erroneous satellite {sv:s} found'.format(func=cFuncName, sv=colored(sv, 'red')))

        logger.info('   {sv:s}: #Obs = {obs:6d}  PRres = {prmean:+6.3f} +- {prstd:6.3f}, {prlt2p:6.2f} (#{prlt2:5d}) within [-2, +2]'.format(sv=sv, obs=dSV['count'], prmean=dSV['PRmean'], prstd=dSV['PRstd'], prlt2p=dSV['PRlt2%'], prlt2=dSV['PRlt2']))

    dSVList['#GPS'] = nrGPS
    dSVList['#GAL'] = nrGAL
    dSVList['GALList'] = GALList
    dSVList['GPSList'] = GPSList
    dSVList['GALSVs'] = dGALsv
    dSVList['GPSSVs'] = dGPSsv

    return dSVList


def parse_elevation_distribution(dRtk: dict, dfSat: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    parse_elevation_distribution parses the observed resiudals per constellation and per elevation bin of 10 degrees
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: parses observed resiudals as funcion of elevation²'.format(func=cFuncName))

    # define what we use for binning
    gnssLetters = ('E', 'G')
    gnssNames = ('GAL', 'GPS')
    cols = ['Elev', 'PRres', 'CN0']
    # define the bins used
    elev_bins, step = np.linspace(start=0, stop=90, num=7, endpoint=True, retstep=True, dtype=int, axis=0)
    logger.info('{func:s}: elevation bins = {bins!s}'.format(bins=elev_bins, func=cFuncName))
    CN0_bins, step = np.linspace(start=10, stop=70, num=13, endpoint=True, retstep=True, dtype=int, axis=0)
    logger.info('{func:s}: CN0 bins = {bins!s}'.format(bins=CN0_bins, func=cFuncName))
    PRres_bins, step = np.linspace(start=-5, stop=5, num=21, endpoint=True, retstep=True, dtype=float, axis=0)
    tmpArr = np.append(PRres_bins, np.inf)
    PRres_bins = np.append(-np.inf, tmpArr)
    logger.info('{func:s}: PRres bins = {bins!s}'.format(bins=PRres_bins, func=cFuncName))

    # add to dRtk the bins used

    # create dataframe for CN0 / PRres distribution
    dfCN0dist = pd.DataFrame()
    dfPRresdist = pd.DataFrame()

    # calculate the number of PRres within [-2,+2] and CN0 statistics over the elevation bins
    for gnssLetter, gnssName in zip(gnssLetters, gnssNames):
        # create a dataframe to work on
        dfGNSS = dfSat[dfSat['SV'].str.startswith(gnssLetter)][cols]

        if len(dfGNSS.index):
            # display frame for this system
            amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfGNSS, dfName=gnssName)

            # go over the elevation bins
            for elev_min, elev_max in zip(elev_bins[:-1], elev_bins[1:]):
                dfGNSS['elevbin'] = dfGNSS.Elev.between(elev_min, elev_max, inclusive=True)

                amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfGNSS, dfName='{syst:s} in [{min:d}..{max:d}] deg'.format(syst=gnssName, min=elev_min, max=elev_max))

                # create a distribution for PRres
                dfPRresdist['{syst:s}[{min:d}..{max:d}]'.format(syst=gnssName, min=elev_min, max=elev_max)] = pd.cut(dfGNSS.loc[dfGNSS['elevbin']]['PRres'], bins=PRres_bins).value_counts(sort=False)

                # create a distribution for CN0
                dfCN0dist['{syst:s}[{min:d}..{max:d}]'.format(syst=gnssName, min=elev_min, max=elev_max)] = pd.cut(dfGNSS.loc[dfGNSS['elevbin']]['CN0'], bins=CN0_bins).value_counts(sort=False)

            # reduce the values to percentage based on observations taken over all bins
            dsPRres_per_bin = dfPRresdist.loc[:, dfPRresdist.columns].sum()
            PRres_total = dsPRres_per_bin.sum() / 100

            dsCN0_per_bin = dfCN0dist.loc[:, dfCN0dist.columns].sum()
            CN0_total = dsCN0_per_bin.sum() / 100

            # report the distibutions of CN0 and PRres to the user
            amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfPRresdist, dfName='dfPRresdist')
            amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfPRresdist / PRres_total, dfName='dfPRresdist in percentage')
            logger.info('{func:s}: PRres totals per elev bin = \n{bins!s}'.format(bins=dsPRres_per_bin, func=cFuncName))

            amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfCN0dist, dfName='dfCN0dist')
            amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfCN0dist / CN0_total, dfName='dfCN0dist in percentage')
            logger.info('{func:s}: CN0 totals per elev bin = \n{bins!s}'.format(bins=dsCN0_per_bin, func=cFuncName))

    return dfCN0dist, dsCN0_per_bin, dfPRresdist, dsPRres_per_bin


def calcDOPs(dfSats: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    calculates the number of SVs used and corresponding DOP values
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating number of SVs in PVT and DOP values'.format(func=cFuncName))

    # calculate sin/cos of elevation/azimuth
    dfSats['sinEl'] = np.sin(np.deg2rad(dfSats.Elev))
    dfSats['cosEl'] = np.cos(np.deg2rad(dfSats.Elev))
    dfSats['sinAz'] = np.sin(np.deg2rad(dfSats.Azim))
    dfSats['cosAz'] = np.cos(np.deg2rad(dfSats.Azim))

    # calculate the direction cosines for each satellite
    dfSats['alpha'] = dfSats['cosEl'] * dfSats['sinAz']
    dfSats['beta'] = dfSats['cosEl'] * dfSats['cosAz']
    dfSats['gamma'] = dfSats['sinEl']

    amc.logDataframeInfo(df=dfSats, dfName='dfSats', callerName=cFuncName, logger=logger)

    # get count of SVs
    dfSVCount = countSVs(dfSVs=dfSats, logger=logger)
    amc.logDataframeInfo(df=dfSVCount, dfName='dfSVCount', callerName=cFuncName, logger=logger)

    # calculating DOP is time consumig, so thin down the TOWs
    naTOWs4DOP = getTOWs4DOP(dfNrSVs=dfSVCount, logger=logger)
    logger.debug('{func:s} TOWs for calculating DOPs = {array!s}'.format(func=cFuncName, array=naTOWs4DOP))

    # create a dataframe for DOP values containing the DateTime column (unique values)
    dfDOPs = pd.DataFrame(naTOWs4DOP, columns=['DT'])
    amc.logDataframeInfo(df=dfDOPs, dfName='dfDOPs start', callerName=cFuncName, logger=logger)

    # select the #SVs from dfSVCount for the intervals we use for DOP calculation
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfSVCount, dfName='dfSVCount')
    dfNrSVs4DOP = dfSVCount.loc[dfSVCount['DT'].isin(naTOWs4DOP)]
    dfNrSVs4DOP.reset_index(inplace=True)
    amc.logDataframeInfo(df=dfNrSVs4DOP, dfName='dfNrSVs4DOP', callerName=cFuncName, logger=logger)

    # merge last column with #SVs into dfDops
    dfDOPs.loc[:, '#SVs'] = dfNrSVs4DOP['#SVs']

    # add NA columns for xDOP values
    dfDOPs = dfDOPs.reindex(columns=dfDOPs.columns.tolist() + ['HDOP', 'VDOP', 'PDOP', 'GDOP'])
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfDOPs, dfName='dfDOPs')

    # iterate over all unique TOWs to determine corresponding xDOP values
    logger.info('{func:s}: calculating xDOP values for {epochs:d} epochs'.format(func=cFuncName, epochs=len(naTOWs4DOP)))

    for i, DT in enumerate(naTOWs4DOP):
        # get the index for each DT we have so that we can select the direction cosines associated
        # DT = '2019-04-10 00:00:00'
        # dt = DT.strptime('%Y-%m-%d %H:%M:%S')
        # print('DT = {!s}   {!s}'.format(DT, type(DT)))
        # print('np.datetime64(DT) = {!s}   {!s}'.format(np.datetime64(DT), type(np.datetime64(DT))))
        # print('dfSats[DT].iloc[0] = {!s}   {!s}'.format(dfSats['DT'].iloc[0], type(dfSats['DT'].iloc[0])))

        towIndices = dfSats.index[dfSats['DT'] == np.datetime64(DT)].tolist()
        # print('towIndices = {!s}'.format(towIndices))

        # create matrix with the direction cosines
        dfTOW = dfSats[['alpha', 'beta', 'gamma']].iloc[towIndices]
        dfTOW['delta'] = 1.
        A = dfTOW.to_numpy()
        # print('dfTOW = {!s}'.format(dfTOW))
        # print('dfTOW = {!s}'.format(type(dfTOW)))

        # invert ATA and retain the diagonal squared
        ATAinvDiag = np.linalg.inv(A.transpose().dot(A)).diagonal()
        sqDiag = np.square(ATAinvDiag)
        # print('ATAinvDiag = \n{!s}  \n{!s}'.format(ATAinvDiag, type(ATAinvDiag)))
        # print('sqDiag = \n{!s}  \n{!s}'.format(sqDiag, type(sqDiag)))

        # get the index for this DT into the dfDOPs
        indexTOW = dfDOPs.index[dfDOPs['DT'] == DT].tolist()[0]
        # print('index DT = {!s}'.format(indexTOW))

        # calculate the xDOP values and store them in the dfDOPs
        PDOP = np.sqrt(sqDiag[0] + sqDiag[1] + sqDiag[2])

        dfDOPs.HDOP.iloc[indexTOW] = np.sqrt(sqDiag[0] + sqDiag[1])
        dfDOPs.VDOP.iloc[indexTOW] = ATAinvDiag[2]
        dfDOPs.PDOP.iloc[indexTOW] = PDOP
        dfDOPs.GDOP.iloc[indexTOW] = np.sqrt(sqDiag[0] + sqDiag[1] + sqDiag[2] + sqDiag[3])

        # print('dfDOPS.iloc[indexTOW] = {!s}'.format(dfDOPs.iloc[indexTOW]))

        # show progress bar
        progbar(i, len(naTOWs4DOP), 60)

    print()  # empty print statement for ending progbar
    # drop the cos/sin & direction cosines columns from dfSats
    dfSats.drop(['sinEl', 'cosEl', 'sinAz', 'cosAz', 'alpha', 'beta', 'gamma'], axis=1, inplace=True)

    amc.logDataframeInfo(df=dfDOPs, dfName='dfDOPs (end)', callerName=cFuncName, logger=logger)
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfDOPs, dfName='dfDOPs')

    return dfDOPs


def parseClockBias(statsClk: tempfile._TemporaryFileWrapper, logger: logging.Logger) -> pd.DataFrame:
    """
    parse the clock file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: parsing RTKLib clock statistics {file:s}'.format(func=cFuncName, file=statsClk.name))

    # # read in the satellite status file
    # print('colNames = {!s}'.format(rtkc.dRTKPosStat['Clk']['colNames']))
    # print('useNames = {!s}'.format(rtkc.dRTKPosStat['Clk']['useCols']))

    # with open(statsClk.name, 'r') as fstat:
    #     i = 0
    #     for line in fstat:
    #         print(line, end='')
    #         i = i + 1
    #         if i == 10:
    #             break

    # input("Press Enter to continue...")

    # read in the satellite status file
    dfCLKs = pd.read_csv(statsClk.name, header=None, sep=',', usecols=[*range(1, 9)])
    dfCLKs.columns = rtkc.dRTKPosStat['Clk']['useCols']
    amutils.printHeadTailDataFrame(df=dfCLKs, name='dfCLKs range')

    # # read in the satellite status file
    # dfCLKs = pd.read_csv(statsClk.name, header=None, sep=',', names=rtkc.dRTKPosStat['Clk']['colNames'], usecols=rtkc.dRTKPosStat['Clk']['useCols'])

    # amc.logDataframeInfo(df=dfCLKs, dfName='dfCLKs', callerName=cFuncName, logger=logger)

    # replace the headers
    cols = np.asarray(rtkc.dRTKPosStat['Clk']['useCols'][-4:])
    # if value of clk parameters is 0 replace by NaN
    dfCLKs[cols] = dfCLKs[cols].replace({0: np.nan})
    # add DateTime
    dfCLKs['DT'] = dfCLKs.apply(lambda x: gpstime.UTCFromWT(x['WNC'], x['TOW']), axis=1)

    amc.logDataframeInfo(df=dfCLKs, dfName='dfCLKs', callerName=cFuncName, logger=logger)

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfCLKs, dfName='dfCLKs')

    return dfCLKs


def progbar(curr, total, full_progbar):
    frac = curr / total
    filled_progbar = round(frac * full_progbar)
    print('\r', '#' * filled_progbar + '-' * (full_progbar - filled_progbar), '[{:>7.1%}]'.format(frac), end='')


def countSVs(dfSVs: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    get a count of SVs for each TOW and determine the difference between these counts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    dfCountSVs = pd.DataFrame(dfSVs.groupby('DT').size())

    amc.logDataframeInfo(df=dfCountSVs, dfName='dfCountSVs', callerName=cFuncName, logger=logger)

    dfCountSVs.reset_index(inplace=True)
    dfCountSVs.columns = ['DT', '#SVs']

    # find jumps in number of sats whic introduces a change in DOP values
    dfCountSVs['dSVs'] = dfCountSVs['#SVs'].diff()

    amc.logDataframeInfo(df=dfCountSVs, dfName='dfCountSVs', callerName=cFuncName, logger=logger)

    return dfCountSVs


def getTOWs4DOP(dfNrSVs: pd.DataFrame, logger: logging.Logger) -> np.ndarray:
    """
    getTOWs4DOP selects
    - eveny spread TOWs so that max 1440 DOPs are calculated per session
    - the TOWs at and just before the #SVs changes
    returns a numpy array with these TOWs for calculating DOP
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # dtermine the interval and number of epochs
    stepTOWs = 4800

    # get index for every stepTOWs row
    naSteppedIndex = dfNrSVs.iloc[::stepTOWs].index.tolist()
    naSteppedIndex.append(dfNrSVs.index[-1])

    # serach for TOWs at the changes in number of SVs
    indexSVChanges = dfNrSVs.dSVs.to_numpy().nonzero()[0]
    index2SVChanges = indexSVChanges[indexSVChanges != 0] - 1  # eoch before change in number of SVs

    # combine these indices
    naIndexSVChanges = np.concatenate([indexSVChanges, index2SVChanges, naSteppedIndex])

    # sort the indexes
    naIndexSVChangesSorted = np.unique(np.sort(naIndexSVChanges))

    naTOWs4DOP = dfNrSVs['DT'].values[naIndexSVChangesSorted]  # .strftime('%Y-%m-%d %H:%M:%S')
    # print('naTOWs4DOP.iloc[0] = {!s}  {:d}  {!s}\n'.format(naTOWs4DOP[0], len(naTOWs4DOP), type(naTOWs4DOP)))

    logger.debug('{func:s}: numpy array naTOWs4DOP #{size:d} type = {type!s}\n {array!s}  '.format(func=cFuncName, array=naTOWs4DOP, size=len(naTOWs4DOP), type=type(naTOWs4DOP)))

    return naTOWs4DOP


def addPDOPStatistics(dRtk: dict, dfPos: pd.DataFrame, logger: logging.Logger):
    """
    add the statistics for PDOP bins for E, N and U coordinates
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: add the statistics for PDOP bins for E, N and U coordinates'.format(func=cFuncName))

    # go over the different bin values
    for i in range(len(dRtk['PDOP']['bins']) - 1):
        binInterval = 'bin{:d}-{:.0f}'.format(dRtk['PDOP']['bins'][i], dRtk['PDOP']['bins'][i + 1])
        logger.debug('{func:s}: binInterval = {bin!s}'.format(bin=binInterval, func=cFuncName))

        # create the dict for this PDOP interval
        dRtk['PDOP'][binInterval] = {}
        # find index for the diffrerent PDOP bins selected
        index4Bin = (dfPos['PDOP'] > dRtk['PDOP']['bins'][i]) & (dfPos['PDOP'] <= dRtk['PDOP']['bins'][i + 1])

        dRtk['PDOP'][binInterval]['perc'] = index4Bin.mean()

        # determine the statistics we want for each coordinate
        for j, posCrd in enumerate(['UTM.N', 'UTM.E', 'ellH']):  # lat       lon      ellH
            dCrd = {}

            dCrd['mean'] = dfPos.loc[index4Bin, posCrd].mean()
            dCrd['stddev'] = dfPos.loc[index4Bin, posCrd].std()
            dCrd['min'] = dfPos.loc[index4Bin, posCrd].min()
            dCrd['max'] = dfPos.loc[index4Bin, posCrd].max()

            dRtk['PDOP'][binInterval][posCrd] = dCrd

            logger.debug('{func:s}: in {bin:s} statistics for {crd:s} are {stat!s}'.format(func=cFuncName, bin=binInterval, crd=posCrd, stat=dCrd))

    # add also for all witin bin of [0..6]
    dRtk['PDOP']['PDOPlt6'] = {}

    indexBin06 = (dfPos['PDOP'] <= 6)
    dRtk['PDOP']['PDOPlt6']['perc'] = indexBin06.mean()

    for j, posCrd in enumerate(['UTM.N', 'UTM.E', 'ellH']):  # lat       lon      ellH
        dCrd = {}

        dCrd['mean'] = dfPos.loc[indexBin06, posCrd].mean()
        dCrd['stddev'] = dfPos.loc[indexBin06, posCrd].std()
        dCrd['min'] = dfPos.loc[indexBin06, posCrd].min()
        dCrd['max'] = dfPos.loc[indexBin06, posCrd].max()

        dRtk['PDOP']['PDOPlt6'][posCrd] = dCrd

        logger.debug('{func:s}: in bin0-6 statistics for {crd:s} are {stat!s}'.format(func=cFuncName, crd=posCrd, stat=dCrd))
