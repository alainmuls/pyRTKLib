import sys
import os
import logging
from termcolor import colored
import pandas as pd
from typing import Tuple
from datetime import datetime
from datetimerange import DateTimeRange
import numpy as np

import am_config as amc
from ampyutils import amutils

__author__ = 'amuls'


def read_obs_tabular(gnss: str, logger: logging.Logger) -> pd.DataFrame:
    """
    read_obs_tabular reads the observation data into a dataframe
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # check that th erequested OBSTAB file is present
    gnss_obstab = os.path.join(amc.dRTK['options']['rnx_dir'], 'gfzrnx', amc.dRTK['json']['rnx']['gnss'][gnss]['marker'], amc.dRTK['json']['rnx']['gnss'][gnss]['obstab'])

    print('gnss_obstab = {!s}'.format(gnss_obstab))

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
    # lst_time = [datetime.strptime(dt.strftime('%H:%M:%S'), '%H:%M:%S').time() for dt in df_tmp['DATE_TIME']]
    # df_tmp.loc[:, 'time'] = lst_time

    # dt_arc_start = pd.to_datetime(df_tmp['DATE_TIME']).tolist()

    dt_arc_start = [datetime.strptime(dt.strftime('%H:%M:%S'), '%H:%M:%S').time() for dt in df_tmp['DATE_TIME']]
    print('dt_arc_start = {!s}'.format(dt_arc_start))

    df_tmp = df_prn.loc[idx_arc_end][['DATE_TIME']]
    # dt_arc_end = pd.to_datetime(df_tmp['DATE_TIME']).tolist()
    dt_arc_end = [datetime.strptime(dt.strftime('%H:%M:%S'), '%H:%M:%S').time() for dt in df_tmp['DATE_TIME']]
    print('dt_arc_end = {!s}'.format(dt_arc_end))

    logger.info('{func:s}:    nominal observation interval for {prn:s} = {tint:f}'.format(prn=colored(prn, 'green'), tint=nominal_interval, func=cFuncName))
    # logger.info('{func:s}:    {prn:s} rises at:\n{arcst!s}'.format(prn=colored(prn, 'green'), arcst=df_prn.loc[idx_arc_end][['DATE_TIME', 'PRN', 'gap']], func=cFuncName))
    # logger.info('{func:s}:    {prn:s} sets at:\n{arcend!s}'.format(prn=colored(prn, 'green'), arcend=df_prn.loc[idx_arc_end][['DATE_TIME', 'PRN', 'gap']], func=cFuncName))

    for i, (stdt, enddt) in enumerate(zip(dt_arc_start, dt_arc_end)):
        logger.info('{func:s}:       arc[{nr:d}]: {stdt:s} -> {enddt:s}'.format(nr=i, stdt=colored(stdt.strftime('%H:%M:%S'), 'yellow'), enddt=colored(enddt.strftime('%H:%M:%S'), 'yellow'), func=cFuncName))

    # copy the gap column for this PRN into original df
    df_obstab.loc[df_prn.index, 'gap'] = df_prn['gap']

    return nominal_interval, dt_arc_start, dt_arc_end, obs_arc_count


def intersect_arcs(df_rs: pd.DataFrame, logger: logging.Logger) -> Tuple[int, pd.DataFrame]:
    """
    intersect_arcs determines which observation intervals belong to which TLE interval
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # number of arcs according to observations
    nr_arcs_obs = []
    for prn in df_rs.index:
        # find maximum number of arcs in observations
        nr_arcs_obs.append(longest(df_rs.loc[prn]['obs_arc_count']))
    logger.info('{func:s}:     number of observed arcs per prn: {arcs!s}'.format(arcs=nr_arcs_obs, func=cFuncName))

    # find number of ars per PRN from TLE
    nr_arcs_tle = []
    for prn in df_rs.index:
        # find maximum number of arcs in observations
        nr_arcs_tle.append(longest(df_rs.loc[prn]['tle_arc_count']))
    nr_arcs = max(nr_arcs_tle)
    logger.info('{func:s}:    number of predicted arcs per prn: {arcs!s}'.format(arcs=nr_arcs_tle, func=cFuncName))

    # make the arcs fit together by comparing the start / end dates between observed and TLEs
    df_rs['intersect'] = pd.Series(dtype=object)

    J2000 = datetime(2000, 1, 1)
    for i_prn, prn in enumerate(df_rs.index):
        logger.info('{func:s}: PRN {prn:s}'.format(prn=prn, func=cFuncName))
        prn_intersect = [np.nan] * nr_arcs_obs[i_prn]

        for i_tle, (tle_rise, tle_set) in enumerate(zip(df_rs.loc[prn]['tle_rise'], df_rs.loc[prn]['tle_set'])):
            tle_range = DateTimeRange(datetime.combine(J2000, tle_rise), datetime.combine(J2000, tle_set))
            tle_range.start_time_format = '%H:%M:%S'
            tle_range.end_time_format = '%H:%M:%S'
            logger.info('{func:s}:    tle_range = {tler!s}'.format(tler=tle_range, func=cFuncName))
            for i_obs, (obs_start, obs_end) in enumerate(zip(df_rs.loc[prn]['obs_rise'], df_rs.loc[prn]['obs_set'])):
                obs_range = DateTimeRange(datetime.combine(J2000, obs_start), datetime.combine(J2000, obs_end))
                obs_range.start_time_format = '%H:%M:%S'
                obs_range.end_time_format = '%H:%M:%S'
                logger.info('{func:s}:       obs_range = {obsr!s}  intersect = {int!s}'.format(obsr=obs_range, int=tle_range.is_intersection(obs_range), func=cFuncName))

                if tle_range.is_intersection(obs_range):
                    prn_intersect[i_obs] = i_tle

        # store in the itersection column
        df_rs.loc[prn, 'intersect'] = prn_intersect

    return nr_arcs, df_rs


def rearrange_arcs(nr_arcs: int, df_rs: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    rearrange_arcs creates a dataframe containing the number of observations (observed / TLE) per arc
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create an empty dataframe for collecting the information per arc
    lst_arcs = ['Arc{:d}_obs'.format(i) for i in range(nr_arcs)] + ['Arc{:d}_tle'.format(i) for i in range(nr_arcs)] + ['Arc{:d}_%'.format(i) for i in range(nr_arcs)]
    df_arcs = pd.DataFrame(columns=['PRN'] + lst_arcs)

    # determine the observations vs predicted per arc
    for i_prn, prn in enumerate(df_rs.index):
        nr_arc_obs = []
        nr_arc_tle = []

        for i_arc in range(nr_arcs):
            # determine the observations done per arc
            lst_obs2sum = [i for i in range(len(df_rs.loc[prn]['intersect'])) if df_rs.loc[prn]['intersect'][i] == i_arc]

            lst_prn_obs = [df_rs.loc[prn]['obs_arc_count'][index] for index in lst_obs2sum]
            nr_arc_obs.append(sum(lst_prn_obs))

            # determine the predicted number of observations by TLE
            if i_arc < len(df_rs.loc[prn]['tle_arc_count']):
                nr_arc_tle.append(int(df_rs.loc[prn]['tle_arc_count'][i_arc]))
            else:
                nr_arc_tle.append(0)

        # add to dataframe
        a_series = pd.Series([prn] + nr_arc_obs + nr_arc_tle, index=df_arcs.columns[:7])
        df_arcs = df_arcs.append(a_series, ignore_index=True)

        # determine the percentage of observations
        nr_arc_perc = [float(obs) / float(tle) if tle > 0 else np.nan for obs, tle in zip(nr_arc_obs, nr_arc_tle)]
        df_arcs.iloc[i_prn, 7:] = nr_arc_perc

    logger.info('{func:s}: number of observations vs TLE predicted\n{nrobs!s}'.format(nrobs=df_arcs, func=cFuncName))

    return df_arcs


def longest(a):
    return max(len(a), *map(longest, a)) if isinstance(a, list) and a else 0
