#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import logging
import json
import glob
import numpy as np
from shutil import copyfile
import pandas as pd
from skyfield import api as sf
from datetime import datetime, timedelta

import am_config as amc
from gfzrnx import rnxobs_tabular
from ampyutils import amutils
from plot import plot_obstab
from tle import tle_parser

__author__ = 'amuls'


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
        for log_action in log_actions:
            if log_action not in choices:
                raise argparse.ArgumentError(self, "log_actions must be in {!s}".format(choices))
        setattr(namespace, self.dest, log_actions)


class multiplier_action(argparse.Action):
    def __call__(self, parser, namespace, multiplier, option_string=None):
        if not 1 <= int(multiplier) <= 120:
            raise argparse.ArgumentError(self, "multiplier must be in 1..120 times nominal observation interval")
        setattr(namespace, self.dest, multiplier)


class cutoff_action(argparse.Action):
    def __call__(self, parser, namespace, cutoff, option_string=None):
        if not -10 <= int(cutoff) <= 60:
            raise argparse.ArgumentError(self, "cutoff must be lower than 60 degrees, higher than -10 degrees")
        setattr(namespace, self.dest, cutoff)


def treatCmdOpts(argv: list):
    """
    Treats the command line options
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = baseName + ' processes the observation tabular file *.obstab'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-d', '--dir', help='Directory with RINEX files (default {:s})'.format(colored('.', 'green')), required=False, type=str, default='.')
    parser.add_argument('-g', '--gnss', help='Which GNSS observation tabular to process', choices=['E', 'G'], required=True, type=str)
    parser.add_argument('-c', '--cutoff', help='minimal cutoff angle (default 0 deg)', required=False, default=0, type=int, action=cutoff_action)
    parser.add_argument('-m', '--multiplier', help='multiplier of nominal interval for gap detection', default=30, type=int, action=multiplier_action)

    parser.add_argument('-p', '--plots', help='displays interactive plots (default True)', action='store_true', required=False, default=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.gnss, args.cutoff, args.multiplier, args.plots, args.logging


def checkValidityArgs(dir_rnx: str, logger: logging.Logger) -> bool:
    """
    checks for existence of dirs/files
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # change to baseDir, everything is relative to this directory
    logger.info('{func:s}: check existence of RINEX dir {rnxd:s}'.format(rnxd=dir_rnx, func=cFuncName))
    dir_rnx = os.path.expanduser(dir_rnx)
    if not os.path.exists(dir_rnx):
        logger.error('{func:s}   !!! Dir {basedir:s} does not exist.'.format(basedir=dir_rnx, func=cFuncName))
        return amc.E_INVALID_ARGS

    return amc.E_SUCCESS


def read_json(dir_rnx: str, logger: logging.Logger):
    """
    read_json reads the logged json file that was processed by pyconvbin
    """
    # cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # read the JSON file created by processing pyconvbin.py
    json_name = glob.glob(os.path.join(dir_rnx, '*.json'))[0]

    with open(json_name) as f:
        amc.dRTK = json.load(f)

    pass


def main(argv):
    """
    pyconvbin converts raw data from SBF/UBlox to RINEX

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # treat command line options
    rnx_dir, gnss, cutoff, multiplier, showPlots, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=rnx_dir, logLevels=logLevels)

    logger.info('{func:s}: arguments processed: {args!s}'.format(args=rnx_dir, func=cFuncName))

    # check validity of passed arguments
    retCode = checkValidityArgs(dir_rnx=rnx_dir, logger=logger)
    if retCode != amc.E_SUCCESS:
        logger.error('{func:s}: Program exits with code {error:s}'.format(error=colored('{!s}'.format(retCode), 'red'), func=cFuncName))
        sys.exit(retCode)

    # store parameters
    amc.dRTK = {}
    # get the information from pyconvbin created json file
    read_json(dir_rnx=rnx_dir, logger=logger)

    # load the requested OBSTAB file into a pandas dataframe
    df_obs = rnxobs_tabular.read_obs_tabular(gnss=gnss, logger=logger)
    df_obs['gap'] = np.nan

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_obs, dfName='df_obs')
    # get unique list of PRNs in dataframe
    prn_lst = sorted(df_obs['PRN'].unique())
    logger.info('{func:s}: observed PRNs are {prns!s} (#{total:d})'.format(prns=prn_lst, total=len(prn_lst), func=cFuncName))

    logger.info('{func:s}; getting corresponding NORAD info'.format(func=cFuncName))

    # read the files galileo-NORAD-PRN.t and gps-ops-NORAD-PRN.t
    dfNORAD = tle_parser.read_norad2prn(logger=logger)
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfNORAD, dfName='dfNORAD')

    # get the corresponding NORAD nrs for the given PRNs
    dNORADs = tle_parser.get_norad_numbers(prns=prn_lst, dfNorad=dfNORAD, logger=logger)
    logger.info('{func:s}: corresponding NORAD nrs (#{count:d}):'.format(count=len(dNORADs), func=cFuncName))

    # load a time scale and set RMA as Topo
    # loader = sf.Loader(dir_tle, expire=True)  # loads the needed data files into the tle dir
    ts = sf.load.timescale()
    RMA = sf.Topos('50.8438 N', '4.3928 E')
    logger.info('{func:s}: Earth station RMA @ {topo!s}'.format(topo=colored(RMA, 'green'), func=cFuncName))
    # get the datetime that corresponds to yydoy
    date_yydoy = datetime.strptime(amc.dRTK['rnx']['times']['DT'], '%Y-%m-%d %H:%M:%S')
    yydoy = date_yydoy.strftime('%y%j')
    logger.info('{func:s}: calculating rise / set times for {date:s} ({yydoy:s})'.format(date=colored(date_yydoy.strftime('%d-%m-%Y'), 'green'), yydoy=yydoy, func=cFuncName))

    t0 = ts.utc(int(date_yydoy.strftime('%Y')), int(date_yydoy.strftime('%m')), int(date_yydoy.strftime('%d')))
    date_tomorrow = date_yydoy + timedelta(days=1)
    t1 = ts.utc(int(date_tomorrow.strftime('%Y')), int(date_tomorrow.strftime('%m')), int(date_tomorrow.strftime('%d')))

    # find corresponding TLE record for NORAD nrs
    df_tles = tle_parser.find_norad_tle_yydoy(dNorads=dNORADs, yydoy=yydoy, logger=logger)

    # list of rise / set times by observation / TLEs
    lst_obs_rise = []

    # find in observations and by TLEs what the riuse/set times are and number of observations
    for prn in prn_lst:
        # find rise & set times for each SV and store into list dt_obs_rise_set and dt_obs_set
        nom_interval, dt_obs_rise, dt_obs_set, obs_arc_count = rnxobs_tabular.rise_set_times(prn=prn, df_obstab=df_obs, nomint_multi=multiplier, logger=logger)

        # find rise:set times using TLEs
        dt_tle_rise, dt_tle_set, dt_tle_cul, tle_arc_count = tle_parser.tle_rise_set_times(prn=prn, df_tle=df_tles, marker=RMA, t0=t0, t1=t1, elev_min=cutoff, obs_int=nom_interval, logger=logger)

        # add to list for creating dataframe
        lst_obs_rise.append([dt_obs_rise, dt_obs_set, obs_arc_count, dt_tle_rise, dt_tle_set, dt_tle_cul, tle_arc_count])

    # test to import in dataframe
    df_rise_set_tmp = pd.DataFrame(lst_obs_rise, columns=['obs_rise', 'obs_set', 'obs_arc_count', 'tle_rise', 'tle_set', 'tle_cul', 'tle_arc_count'], index=prn_lst)

    # find corresponding arcs between observation and predicted TLE
    max_arcs, df_rise_set = rnxobs_tabular.intersect_arcs(df_rs=df_rise_set_tmp, logger=logger)

    # inform user
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_rise_set, dfName='df_rise_set')
    # write to csv file
    csvName = os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker'], 'rise-set-dt.csv')
    df_rise_set.to_csv(csvName, index=None, header=True)

    # create a new dataframe that has PRNs as index and the max_arcs columns with number of obs / TLEs
    df_obs_arcs = rnxobs_tabular.rearrange_arcs(nr_arcs=max_arcs, df_rs=df_rise_set, logger=logger)
    # write to csv file
    csvName = os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker'], 'obs_arcs.csv')
    df_obs_arcs.to_csv(csvName, index=None, header=True)

    # plot the statistics of observed vs TLE predicted
    plot_obstab.plot_rise_set_times(gnss=gnss, df_rs=df_rise_set, logger=logger, showplot=showPlots)
    plot_obstab.plot_rise_set_stats(gnss=gnss, df_arcs=df_obs_arcs, nr_arcs=max_arcs, logger=logger, showplot=showPlots)

    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_obs[(df_obs['gap'] > 1.) | (df_obs['gap'].isna())], dfName='df_obs', head=50)

    # logger.info('{func:s}: amc.dRTK =\n{json!s}'.format(json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor), func=cFuncName))

    # copy temp log file to the YYDOY directory
    copyfile(log_name, os.path.join(os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker']), 'pyobstab.log'))
    os.remove(log_name)


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
