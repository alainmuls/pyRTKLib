#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import pickle
import json
import logging
import pathlib
import pandas as pd
from shutil import copyfile
import math

import am_config as amc
from ampyutils import amutils
from glab import glab_parser, glab_plot_output, glab_statistics
from glab import glab_constants as glc

__author__ = 'amuls'


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
        for log_action in log_actions:
            if log_action not in choices:
                raise argparse.ArgumentError(self, "log_actions must be in {!s}".format(choices))
        setattr(namespace, self.dest, log_actions)


class scale_action(argparse.Action):
    def __call__(self, parser, namespace, scale_action, option_string=None):
        base_choices = [1, 2, 5]
        scale_choices = [.1, 1, 10, 100, 1000]
        all_choices = []
        for s in scale_choices:
            all_choices += [b * s for b in base_choices]
        if scale_action not in all_choices:
            raise argparse.ArgumentError(self, "scale_action must be in {!s}".format(all_choices))
        setattr(namespace, self.dest, scale_action)


class center_action(argparse.Action):
    def __call__(self, parser, namespace, center_action, option_string=None):
        choices = ['origin', 'wavg']
        if center_action not in choices:
            raise argparse.ArgumentError(self, "center_action must be in {!s}".format(choices))
        setattr(namespace, self.dest, center_action)


def treatCmdOpts(argv):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = amc.cBaseName + ' plots gLAB (v6) receiver position'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-d', '--dir', help='Root directory (default {:s})'.format(colored('.', 'green')), required=False, type=str, default='.')
    parser.add_argument('-f', '--file', help='gLAB processed out file', required=True, type=str)
    # parser.add_argument('-r', '--resFile', help='RTKLib residuals file', type=str, required=False, default=None)
    # parser.add_argument('-m', '--marker', help='Geodetic coordinates (lat,lon,ellH) of reference point in degrees: 50.8440152778 4.3929283333 151.39179 for RMA, 50.93277777 4.46258333 123 for Peutie, default 0 0 0 means use mean position', nargs=3, type=str, required=False, default=["0", "0", "0"])
    parser.add_argument('-s', '--scale', help='display ENU plots with +/- this scale range (default 5m)', required=False, default=5, type=float, action=scale_action)
    parser.add_argument('-c', '--center', help='center ENU plots (Select "origin" or "wavg")', required=False, default='origin', type=str, action=center_action)

    parser.add_argument('-p', '--plots', help='displays interactive plots (default True)', action='store_true', required=False, default=False)
    parser.add_argument('-o', '--overwrite', help='overwrite intermediate files (default False)', action='store_true', required=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.file, args.scale, args.center, args.plots, args.overwrite, args.logging


def check_arguments(logger: logging.Logger) -> int:
    """
    check_arguments checks the given arguments wether they are valid. return True or False
    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # check whether the given dir_root exist
    path = pathlib.Path(amc.dRTK['dir_root'])
    if not path.is_dir():
        logger.info('{func:s}: directory {root:s} does not exist'.format(root=colored(amc.dRTK['dir_root'], 'red'), func=cFuncName))
        return amc.E_DIR_NOT_EXIST
    else:  # change to directory
        os.chdir(path)

    # check whether the glab_out exists and is readable
    path = pathlib.Path(amc.dRTK['glab_out'])
    if not path.is_file():
        logger.info('{func:s}: file {file:s} does not exist'.format(file=colored(amc.dRTK['glab_out'], 'red'), func=cFuncName))
        return amc.E_FILE_NOT_EXIST

    return amc.E_SUCCESS


def store_to_cvs(df: pd.DataFrame, ext: str, logger: logging.Logger, index: bool = True):
    """
    store the dataframe to a CSV file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    csv_name = amc.dRTK['glab_out'].split('.')[0] + '.' + ext
    amc.dRTK['dgLABng'][ext] = csv_name

    # make dir if not exist
    dir_glabng = os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'])
    amutils.mkdir_p(dir_glabng)

    df.to_csv(os.path.join(dir_glabng, csv_name), index=index, header=True)

    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df, dfName=csv_name)
    logger.info('{func:s}: stored dataframe as csv file {csv:s}'.format(csv=colored(csv_name, 'yellow'), func=cFuncName))


def main(argv) -> bool:
    """
    glabplotposn plots data from gLAB (v6) OUTPUT messages

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # limit float precision
    # encoder.FLOAT_REPR = lambda o: format(o, '.3f')
    # pd.options.display.float_format = "{:,.3f}".format

    # treat command line options
    dir_root, glab_out, scale_enu, center_enu, show_plot, overwrite, log_levels = treatCmdOpts(argv)

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=dir_root, logLevels=log_levels)

    # store cli parameters
    amc.dRTK = {}
    amc.dRTK['dir_root'] = dir_root
    amc.dRTK['glab_out'] = glab_out

    # create sub dict for gLAB related info
    dgLABng = {}
    dgLABng['dir_glab'] = 'glabng'

    amc.dRTK['dgLABng'] = dgLABng

    # create the DOP bins for plotting
    amc.dRTK['dop_bins'] = [0, 2, 3, 4, 5, 6, math.inf]

    # check some arguments
    ret_val = check_arguments(logger=logger)
    if ret_val != amc.E_SUCCESS:
        sys.exit(ret_val)

    # split gLABs out file in parts
    glab_msgs = glc.dgLab['messages'][0:2]  # INFO & OUTPUT messages needed
    dglab_tmpfiles = glab_parser.split_glab_outfile(msgs=glab_msgs, glab_outfile=amc.dRTK['glab_out'], logger=logger)

    # read in the INFO messages from INFO temp file
    amc.dRTK['INFO'] = glab_parser.parse_glab_info(glab_info=dglab_tmpfiles['INFO'], logger=logger)
    # read in the OUTPUT messages from OUTPUT temp file
    df_output = glab_parser.parse_glab_output(glab_output=dglab_tmpfiles['OUTPUT'], logger=logger)
    # save df_output as CSV file
    store_to_cvs(df=df_output, ext='pos', logger=logger, index=False)

    # calculate statitics
    # gLAB OUTPUT messages
    amc.dRTK['dgLABng']['stats'] = glab_statistics.statistics_glab_outfile(df_outp=df_output, logger=logger)

    # plot the gLABs OUTPUT messages
    glab_plot_output.plot_glab_position(dfCrd=df_output, scale=scale_enu, showplot=show_plot, logger=logger)
    glab_plot_output.plot_glab_scatter(dfCrd=df_output, scale=scale_enu, center=center_enu, showplot=show_plot, logger=logger)
    glab_plot_output.plot_glab_scatter_bin(dfCrd=df_output, scale=scale_enu, center=center_enu, showplot=show_plot, logger=logger)
    glab_plot_output.plot_glab_xdop(dfCrd=df_output, showplot=show_plot, logger=logger)

    # report to the user
    # report to the user
    logger.info('{func:s}: Project information =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    # create pickle file from amc.dRTK
    pickle_out = amc.dRTK['glab_out'].split('.')[0] + '.pickle'
    with open(pickle_out, 'wb') as f:
        pickle.dump(amc.dRTK, f, protocol=pickle.HIGHEST_PROTOCOL)
    logger.info('{func:s}: created pickle file {pickle:s}'.format(func=cFuncName, pickle=colored(pickle_out, 'green')))

    # copy temp log file to the YYDOY directory
    copyfile(log_name, os.path.join(amc.dRTK['dir_root'], '{obs:s}-{prog:s}'.format(obs=amc.dRTK['glab_out'].split('.')[0], prog='output.log')))
    os.remove(log_name)

    return amc.E_SUCCESS


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
