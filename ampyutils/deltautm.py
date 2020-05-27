
import numpy as np
from termcolor import colored
import sys
import logging
import os
import utm

import am_config as amc


def addDeltaUTM(enuRefPt, dfLLH, logger: logging.Logger):
    """
    addDeltaUTM adds the dfference of current position compared to reference location

    :param enuRefPt: (lat,lon) coordinates of reference point
    :type enuRefPt: dictionary
    :param dfLLH: geodetic coordinates of current point
    :type dfLLH: dataframe

    :returns: mean and standard deviation of delta UTM and delta heightcoordinates
    :rtype: 2 dictionaries of float
    """
    # set current function name
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # calculate UTM coordiantes of valid positions
    dfLLH['UTM.E'], dfLLH['UTM.N'], dfLLH['UTM.Z'], dfLLH['UTM.L'] = utm.from_latlon(dfLLH['lat'].to_numpy(), dfLLH['lon'].to_numpy())
    logger.info('{func:s} ... transformed to UTM coordiantes'.format(func=cFuncName))

    # mean delta UTM coordinates
    meanUTM = {}
    meanUTM['UTM.E'] = dfLLH['UTM.E'].mean()
    meanUTM['UTM.N'] = dfLLH['UTM.N'].mean()
    meanUTM['ellH'] = dfLLH['ellH'].mean()
    # stdDev delta UTM coordinates
    stdDevUTM = {}
    stdDevUTM['UTM.E'] = dfLLH['UTM.E'].std()
    stdDevUTM['UTM.N'] = dfLLH['UTM.N'].std()
    stdDevUTM['ellH'] = dfLLH['ellH'].std()

    # # determine the UTM coordinates for the Reference point
    # enuRefPt['UTM.E'], enuRefPt['UTM.N'], enuRefPt['UTM.Z'], enuRefPt['UTM.L'] = utm.from_latlon(enuRefPt['lat'], enuRefPt['lon'])
    # logger.info('{func:s} ... Reference point lat = {lat:.9f}  lon = {lon:.9f}'.format(func=cFuncName, lat=enuRefPt['lat'], lon=enuRefPt['lon']))
    # logger.info('{func:s} ... Reference point UTM = {east:11.3f} {north:11.3f} {zone:02d}{letter:1s}'.format(func=cFuncName, east=enuRefPt['UTM.E'], north=enuRefPt['UTM.N'], zone=enuRefPt['UTM.Z'], letter=enuRefPt['UTM.L']))

    # # determine offset with regard to Reference point in UTM
    # dUTM = {}
    # dUTM['E'] = np.array(dfLLH['UTM.E']) - enuRefPt['UTM.E']
    # dUTM['N'] = np.array(dfLLH['UTM.N']) - enuRefPt['UTM.N']
    # dUTM['h'] = np.array(dfLLH['ellH']) - enuRefPt['ellH']

    logger.info('{func:s} ... UTM.E mean = {mean:.3f} +- {stddev:.3f}'.format(func=cFuncName, mean=meanUTM['UTM.E'], stddev=stdDevUTM['UTM.E']))
    logger.info('{func:s} ... UTM.N mean = {mean:.3f} +- {stddev:.3f}'.format(func=cFuncName, mean=meanUTM['UTM.N'], stddev=stdDevUTM['UTM.N']))
    logger.info('{func:s} ... EllH mean = {mean:.3f} +- {stddev:.3f}'.format(func=cFuncName, mean=meanUTM['ellH'], stddev=stdDevUTM['ellH']))

    return meanUTM, stdDevUTM
