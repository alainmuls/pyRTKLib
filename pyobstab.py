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
from tabulate import tabulate
import pandas as pd

import am_config as amc
from gfzrnx import rnxobs_tabular
from ampyutils import  amutils
from plot import plot_obstab

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
        if not 1 <= int(multiplier) <= 60:
            raise argparse.ArgumentError(self, "multiplier must be in 1..60 times nominal observation interval")
        setattr(namespace, self.dest, multiplier)


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
    parser.add_argument('-m', '--multiplier', help='multiplier of nominal interval for gap detection', default=10, type=int, action=multiplier_action)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.gnss, args.multiplier, args.logging


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
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

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
    rnx_dir, gnss, multiplier, logLevels = treatCmdOpts(argv)

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
    # find rise & set times for each SV and store into list lst_rise_set and lst_set
    lst_rise_set = []
    for prn in prn_lst:
        lst_rise, lst_set = rnxobs_tabular.rise_set_times(prn=prn, df_obstab=df_obs, nomint_multi=multiplier, logger=logger)

        # check if as many rise and set DT found
        if len(lst_rise) == len(lst_set):
            lst_rise_set.append([lst_rise, lst_set])

    # test to import in  dataframe
    df_rise_set = pd.DataFrame(lst_rise_set, columns=['idx_rise', 'idx_set'], index=prn_lst)
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_rise_set, dfName='df_rise_set')

    # write to csv file
    csvName = os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker'], 'rise-set-idx.csv')
    df_rise_set.to_csv(csvName, index=None, header=True)

    # plot the rise-set
    plot_obstab.plot_rise_set_times(gnss=gnss, df_dt=df_obs['DATE_TIME'], df_idx_rs=df_rise_set, logger=logger, showplot=True)

    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_obs, dfName='df_obs', head=50)
    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_obs[(df_obs['gap'] > 1.) | (df_obs['gap'].isna())], dfName='df_obs', head=50)

    logger.info('{func:s}: amc.dRTK =\n{json!s}'.format(json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor), func=cFuncName))

    # copy temp log file to the YYDOY directory
    copyfile(log_name, os.path.join(os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker']), 'pyobstab.log'))
    os.remove(log_name)


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
