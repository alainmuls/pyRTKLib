import pandas as pd
from termcolor import colored
import sys
import numpy as np
import os
import logging
from datetime import datetime
import utm as UTM

from ampyutils import amutils
from GNSS import gpstime
import am_config as amc


def parsePosFile(logger: logging.Logger) -> pd.DataFrame:
    """
    parses 'posn' file created by pyrtklib.py
    """

    # set current function name
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    posFilePath = os.path.join(amc.dRTK['posDir'], amc.dRTK['posFile'])

    logger.info('{func:s} parsing rtk-pos file {posf:s}'.format(func=cFuncName, posf=posFilePath))

    # looking for start times of observation file
    for line in open(posFilePath):
        rec = line.strip()
        if rec.startswith('% obs start'):
            amc.dRTK['obsStart'] = datetime.strptime(rec[14:33], '%Y/%m/%d %H:%M:%S')
            break
    # looking for end times of observation file
    for line in open(posFilePath):
        rec = line.strip()
        if rec.startswith('% obs end'):
            amc.dRTK['obsEnd'] = datetime.strptime(rec[14:33], '%Y/%m/%d %H:%M:%S')
            break
    # looking for ref pos of observation file
    foundRefPos = False
    for line in open(posFilePath):
        rec = line.strip()
        if rec.startswith('% ref pos'):
            amc.dRTK['RefPos'] = [float(x) for x in rec.split(':')[1].split()]
            amc.dRTK['RefPosUTM'] = UTM.from_latlon(amc.dRTK['RefPos'][0], amc.dRTK['RefPos'][1])
            logger.info('{func:s}: reference station coordinates are LLH={llh!s} UTM={utm!s}'.format(func=cFuncName, llh=amc.dRTK['RefPos'], utm=amc.dRTK['RefPosUTM']))
            foundRefPos = True
            break

    if not foundRefPos:
        amc.dRTK['RefPos'] = [np.NaN, np.NaN, np.NaN]
        amc.dRTK['RefPosUTM'] = (np.NaN, np.NaN, np.NaN, np.NaN)
        logger.info('{func:s}: no reference station used'.format(func=cFuncName))

    # find start of results in rtk file
    endHeaderLine = amutils.line_num_for_phrase_in_file('%  GPST', posFilePath)
    dfPos = pd.read_csv(posFilePath, header=endHeaderLine, delim_whitespace=True)
    dfPos = dfPos.rename(columns={'%': 'WNC', 'GPST': 'TOW', 'latitude(deg)': 'lat', 'longitude(deg)': 'lon', 'height(m)': 'ellH', 'sdn(m)': 'sdn', 'sde(m)': 'sde', 'sdu(m)': 'sdu', 'sdne(m)': 'sdne', 'sdeu(m)': 'sdeu', 'sdun(m)': 'sdun', 'age(s)': 'age'})

    # check if we have records for this mode in the data, else exit
    if dfPos.shape[0] == 0:
        logger.info('{func:s}: found no data in pos-file {pos:s}'.format(func=cFuncName, pos=amc.dRTK['posFile']))
        sys.exit(amc.E_FAILURE)

    # store total number of observations
    amc.dRTK['#obs'] = dfPos.shape[0]

    # store number of calculated positions for requested rtk quality
    amc.dRTK['#obsQual'] = len(dfPos.loc[dfPos['Q'] == amc.dRTK['iQual']])

    logger.info('{func:s}: amc.dRTK = \n{drtk!s}'.format(func=cFuncName, drtk=amc.dRTK))

    # convert the time in seconds
    dfPos['DT'] = dfPos.apply(lambda x: gpstime.UTCFromWT(x['WNC'], x['TOW']), axis=1)

    # add UTM coordinates
    dfPos['UTM.E'], dfPos['UTM.N'], dfPos['UTM.Z'], dfPos['UTM.L'] = UTM.from_latlon(dfPos['lat'].to_numpy(), dfPos['lon'].to_numpy())

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfPos, dfName='{posf:s}'.format(posf=posFilePath))

    amc.logDataframeInfo(df=dfPos, dfName='dfPos', callerName=cFuncName, logger=logger)

    return dfPos


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


def stddev(crd: pd.Series, avgCrd: float) -> float:
    """
    stddev calculates the standard deviation of series
    """
    dCrd = crd.subtract(avgCrd)

    return dCrd.std()
