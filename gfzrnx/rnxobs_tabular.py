import sys
import os
import logging
from termcolor import colored
import pandas as pd
from typing import Tuple

import am_config as amc
from ampyutils import amutils

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


def rise_set_times(prn: str, df_obstab: pd.DataFrame, nomint_multi: int, logger: logging.Logger) -> Tuple[int, list, list, list]:
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
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_prn, dfName='df_prn[{:s}]'.format(prn))

    # find the nominal time interval of observations
    nominal_interval = df_prn['gap'].median()
    # find the indices where the interval is bigger than nominal_interval
    # idx_arc_start = df_prn[(df_prn['gap'] > nomint_multi * nominal_interval) | (df_prn['gap'].isna())].index.tolist()
    idx_arc_start = [df_prn.index[0]] + df_prn[df_prn['gap'] > nomint_multi * nominal_interval].index.tolist()
    idx_arc_end = df_prn[df_prn['gap'].shift(-1) > nomint_multi * nominal_interval].index.tolist() + [df_prn.index[-1]]

    # find the number of observations for each arc
    obs_arc_count = []
    for arc_start, arc_end in zip(idx_arc_start, idx_arc_end):
        obs_arc_count.append(prn_loc.get_loc(arc_end) - prn_loc.get_loc(arc_start) + 1)

    # get the corresponding data time info
    df_tmp = df_prn.loc[idx_arc_start][['DATE_TIME']]
    dt_arc_start = pd.to_datetime(df_tmp['DATE_TIME']).tolist()
    df_tmp = df_prn.loc[idx_arc_end][['DATE_TIME']]
    dt_arc_end = pd.to_datetime(df_tmp['DATE_TIME']).tolist()

    logger.info('{func:s}:    nominal observation interval for {prn:s} = {tint:f}'.format(prn=colored(prn, 'green'), tint=nominal_interval, func=cFuncName))
    # logger.info('{func:s}:    {prn:s} rises at:\n{arcst!s}'.format(prn=colored(prn, 'green'), arcst=df_prn.loc[idx_arc_end][['DATE_TIME', 'PRN', 'gap']], func=cFuncName))
    # logger.info('{func:s}:    {prn:s} sets at:\n{arcend!s}'.format(prn=colored(prn, 'green'), arcend=df_prn.loc[idx_arc_end][['DATE_TIME', 'PRN', 'gap']], func=cFuncName))

    for i, (stdt, enddt) in enumerate(zip(dt_arc_start, dt_arc_end)):
        logger.info('{func:s}:       arc[{nr:d}]: {stdt:s} -> {enddt:s}'.format(nr=i, stdt=colored(stdt.strftime('%H:%M:%S'), 'yellow'), enddt=colored(enddt.strftime('%H:%M:%S'), 'yellow'), func=cFuncName))

    # copy the gap column for this PRN into original df
    df_obstab.loc[df_prn.index, 'gap'] = df_prn['gap']

    return nominal_interval, dt_arc_start, dt_arc_end, obs_arc_count
