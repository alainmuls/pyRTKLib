import sys
import os
from datetime import datetime
import logging
from termcolor import colored
import pandas as pd
import numpy as np
from typing import Tuple

import am_config as amc
from ampyutils import  amutils

__author__ = 'amuls'


def read_obs_tabular(gnss: str, logger: logging.Logger) -> pd.DataFrame:
    """
    read_obs_tabular reads the observation data into a dataframe
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # check that th erequested OBSTAB file is present
    gnss_obstab = os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker'], amc.dRTK['rnx']['gnss'][gnss]['obstab'])

    # df = pd.read_csv('gnss_obstab')
    logger.info('{func:s}: reading observation tabular file {obstab:s} (be patient)'.format(obstab=colored(gnss_obstab, 'green'), func=cFuncName))
    try:
        df = pd.read_csv(gnss_obstab, parse_dates=[['DATE', 'TIME']], delim_whitespace=True)
    except FileNotFoundError as e:
        logger.critical('{func:s}: Error = {err!s}'.format(err=e, func=cFuncName))
        sys.exit(amc.E_FILE_NOT_EXIST)

    return df


def rise_set_times(prn: str, df_obstab: pd.DataFrame, nomint_multi: int, logger: logging.Logger) -> Tuple[list, list]:
    """
    rise_set_times determines observed rise and set times for PRN
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # index the rows for this PRN
    prn_loc = df_obstab.loc[df_obstab['PRN'] == prn].index
    # logger.info('{func:s}: Data for {prn:s} are at indices\n{idx!s}'.format(prn=colored(prn, 'green'), idx=prn_loc, func=cFuncName))

    # create a df_prn only using these rows
    df_prn = df_obstab.iloc[prn_loc]
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_prn, dfName='df_prn[{:s}]'.format(prn), head=30)

    # determine the datetime gaps for this PRN
    df_prn['gap'] = (df_prn['DATE_TIME'] - df_prn['DATE_TIME'].shift(1)).astype('timedelta64[s]')
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_prn, dfName='df_prn[{:s}]'.format(prn), head=30)

    # find the nominal time interval of observations
    nominal_interval = df_prn['gap'].median()
    # find the indices where the interval is bigger than nominal_interval
    idx_arc_start = df_prn[(df_prn['gap'] > nomint_multi * nominal_interval) | (df_prn['gap'].isna())].index.tolist()
    idx_arc_start = [df_prn.index[0]] + df_prn[df_prn['gap'] > nomint_multi * nominal_interval].index.tolist()
    idx_arc_end = df_prn[df_prn['gap'].shift(-1) > nomint_multi * nominal_interval].index.tolist() + [df_prn.index[-1]]

    logger.info('{func:s}:    nominal time interval for {prn:s} = {tint:f}'.format(prn=colored(prn, 'green'), tint=nominal_interval, func=cFuncName))
    logger.info('{func:s}:    {prn:s} rises at:\n{arcst!s}'.format(prn=colored(prn, 'green'), arcst=df_prn.loc[idx_arc_start][['DATE_TIME', 'PRN', 'gap']], func=cFuncName))
    logger.info('{func:s}:    {prn:s} sets at:\n{arcend!s}'.format(prn=colored(prn, 'green'), arcend=df_prn.loc[idx_arc_end][['DATE_TIME', 'PRN', 'gap']], func=cFuncName))

    # print(df.loc[[378285, 378286, 378287, 378288, 378289, 378290, 378291, 378292, 378293, 378294]])
    # print(df.loc[[378494, 378495, 378496, 378497, 378498, 378499, 378590, 378591, 378592, 378593, 378594, 378595, 378596, 378597, 378598, 378599, 378600, 378601, 378602, 378603, 378604]])
    # print(df.loc[[378094, 378095, 378096, 378097, 378098, 378099, 378100, 378101, 378102, 378103, 378104, 378105, 378106, 378107, 378108, 378109, 378110, 378111, 378112, 378113, 378114, 378115, 378116, 378117, 378118, 378119, 378120, 378121, 378122, 378123, 378124, 378125, 378126, 378127, 378128, 378129, 378130]])

    # copy the gap column for this PRN into original df
    df_obstab.loc[df_prn.index, 'gap'] = df_prn['gap']

    return idx_arc_start, idx_arc_end
