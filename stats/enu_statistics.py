import sys
import os
import pandas as pd
import logging
from termcolor import colored
import numpy as np
from typing import Tuple

from ampyutils import amutils

__author__ = 'amuls'


def enu_statistics(dRtk: dict, dfENU: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    enu_statistics calculates the statistics of the ENU coordinates passed
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    dfENUStats = dfENU[['dUTM.E', 'dUTM.N', 'dEllH']].describe()
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfENUStats, dfName='dfENUStats')

    # add statistics for UTM coordinate differences
    dENUStats = {}
    for col in ('dUTM.E', 'dUTM.N', 'dEllH'):
        print('col = {:s}'.format(col))
        dCol = {}
        for index, row in dfENUStats.iterrows():
            dCol[index] = row[col]
        dENUStats[col] = dCol

        logger.debug('{func:s}: statistics for {col:s}\n{stat!s}'.format(col=col, stat=dENUStats[col], func=cFuncName))

    # add to global dRTK dict
    dRtk['stats'] = dENUStats

    return dfENUStats


def enupdop_distribution(dRtk: dict, dfENU: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    enupdop_distribution calculates the distribution of the ENU coordinates passed
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the dataframe for the ENU distribution info
    dfENUDist = pd.DataFrame()

    # create the bins used for the difference in UTM/ellH coordinates
    dENU_bins, dENU_step = np.linspace(start=-5, stop=+5, num=21, endpoint=True, retstep=True, dtype=float, axis=0)
    tmpArr = np.append(dENU_bins, np.inf)
    dENU_bins = np.append(-np.inf, tmpArr)
    logger.info('{func:s}: dENU_bins = {bins!s} with step {step:.1f}'.format(bins=dENU_bins, step=dENU_step, func=cFuncName))

    # calculate the distribution for ENU coordinates
    for enu_col in ('dUTM.E', 'dUTM.N', 'dEllH'):
        dfENUDist[enu_col] = pd.cut(dfENU[enu_col], bins=dENU_bins).value_counts(sort=False)

    # create the dataframe for the ENU distribution info
    dfPDOPDist = pd.DataFrame()

    # create the bins for the PDOP
    dop_bins = [0, 2, 3, 4, 5, 6, np.inf]
    logger.info('{func:s}: dop_bins = {bins!s}'.format(bins=dop_bins, func=cFuncName))

    # calculate the distribution for xDOP coordinates
    for dop_col in ('HDOP', 'VDOP', 'PDOP', 'GDOP'):
        dfPDOPDist[dop_col] = pd.cut(dfENU[dop_col], bins=dop_bins).value_counts(sort=False)

    return dfENUDist, dfPDOPDist
