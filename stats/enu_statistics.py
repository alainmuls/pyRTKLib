import sys
import os
import pandas as pd
import logging
from termcolor import colored
import json

from ampyutils import amutils

__author__ = 'amuls'


def enu_statistics(dRtk: dict, dfENU: pd.DataFrame, logger: logging.Logger):
    """
    enu_statistics calculates the distribution of the ENU coordinates passed
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    dfDistENU = dfENU[['dUTM.E', 'dUTM.N', 'dEllH']].describe()
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfDistENU, dfName='dfDistENU')

    # add statistics for UTM coordinate differences
    dDistENU = {}
    for col in ('dUTM.E', 'dUTM.N', 'dEllH'):
        print('col = {:s}'.format(col))
        dCol = {}
        for index, row in dfDistENU.iterrows():
            dCol[index] = row[col]
        dDistENU[col] = dCol

        logger.debug('{func:s}: statistics for {col:s}\n{stat!s}'.format(col=col, stat=dDistENU[col], func=cFuncName))

    # add to global dRTK dict
    dRtk['distENU'] = dDistENU

    logger.info('{func:s}: dRtk =\n{settings!s}'.format(func=cFuncName, settings=json.dumps(dRtk, sort_keys=False, indent=4)))
