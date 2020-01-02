import sys
import os
import pandas as pd
import logging
from termcolor import colored
import json
import numpy as np

from ampyutils import amutils

__author__ = 'amuls'


def enu_statistics(dRtk: dict, dfENU: pd.DataFrame, logger: logging.Logger):
    """
    enu_statistics calculates the statistics of the ENU coordinates passed
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    dfENUStats = dfENU[['dUTM.E', 'dUTM.N', 'dEllH']].describe()
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfENUStats, dfName='dfENUStats')

    # add statistics for UTM coordinate differences
    dDistENU = {}
    for col in ('dUTM.E', 'dUTM.N', 'dEllH'):
        print('col = {:s}'.format(col))
        dCol = {}
        for index, row in dfENUStats.iterrows():
            dCol[index] = row[col]
        dDistENU[col] = dCol

        logger.debug('{func:s}: statistics for {col:s}\n{stat!s}'.format(col=col, stat=dDistENU[col], func=cFuncName))

    # add to global dRTK dict
    dRtk['distENU'] = dDistENU

    logger.info('{func:s}: dRtk =\n{settings!s}'.format(func=cFuncName, settings=json.dumps(dRtk, sort_keys=False, indent=4)))


def enu_distribution(dRtk: dict, dfENU: pd.DataFrame, logger: logging.Logger):
    """
    enu_distribution calculates the distribution of the ENU coordinates passed
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the bins used for the difference in UTM/ellH coordinates
    dENU_bins, dENU_step = np.linspace(start=-5, stop=+5, num=21, endpoint=True, retstep=True, dtype=float, axis=0)
    tmpArr = np.append(dENU_bins, np.inf)
    dENU_bins = np.append(-np.inf, tmpArr)
    logger.info('{func:s}: dENU_bins = {bins!s} with step {step:.1f}'.format(bins=dENU_bins, step=dENU_step, func=cFuncName))

    # name the columns that describe the distribution for the coordinates
    enu_dist_names = ['dist.E', 'dist.N', 'dist.h']
    enu_cols = ['dUTM.E', 'dUTM.N', 'dEllH']

    dfENUDist = pd.DataFrame()

    for enu_col, enu_dist in zip(enu_cols, enu_dist_names):
        dfENUDist[enu_dist] = pd.cut(dfENU[enu_col], bins=dENU_bins).value_counts(sort=False)
        logger.info('{func:s}: distribution for {col:s}\n{dist!s}'.format(col=enu_col, dist=pd.cut(dfENU[enu_col], bins=dENU_bins).value_counts(sort=False), func=cFuncName))

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfENUDist, dfName='dfENUDist', head=23, tail=0)
