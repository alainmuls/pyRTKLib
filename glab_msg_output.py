#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
import logging
import tempfile
from shutil import copyfile
import pathlib
import numpy as np
import pandas as pd

import am_config as amc
from ampyutils import amutils
from glab import glab_parser, glab_plot_output

__author__ = 'amuls'


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
        for log_action in log_actions:
            if log_action not in choices:
                raise argparse.ArgumentError(self, "log_actions must be in {!s}".format(choices))
        setattr(namespace, self.dest, log_actions)


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

    parser.add_argument('-p', '--plots', help='displays interactive plots (default True)', action='store_true', required=False, default=False)
    parser.add_argument('-o', '--overwrite', help='overwrite intermediate files (default False)', action='store_true', required=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.file, args.plots, args.overwrite, args.logging


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


def main(argv) -> bool:
    """
    glabplotposn plots data from gLAB (v6) OUTPUT messages

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # limit float precision
    # encoder.FLOAT_REPR = lambda o: format(o, '.3f')
    pd.options.display.float_format = "{:,.3f}".format

    # treat command line options
    dir_root, glab_out, show_plot, overwrite, log_levels = treatCmdOpts(argv)

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=dir_root, logLevels=log_levels)

    # store cli parameters
    amc.dRTK = {}
    amc.dRTK['dir_root'] = dir_root
    amc.dRTK['glab_out'] = glab_out
    # # set the reference point
    # dMarker = {}
    # dMarker['lat'], dMarker['lon'], dMarker['ellH'] = map(float, posn_marker)
    # print('posn_marker = {!s}'.format(posn_marker))

    # if [dMarker['lat'], dMarker['lon'], dMarker['ellH']] == [0, 0, 0]:
    #     dMarker['lat'] = dMarker['lon'] = dMarker['ellH'] = np.NaN
    #     # dMarker['UTM.E'] = dMarker['UTM.N'] = np.NaN
    #     # dMarker['UTM.Z'] = dMarker['UTM.L'] = ''
    # # else:
    # #     dMarker['UTM.E'], dMarker['UTM.N'], dMarker['UTM.Z'], dMarker['UTM.L'] = utm.from_latlon(dMarker['lat'], dMarker['lon'])
    # amc.dRTK['marker'] = dMarker

    # check some arguments
    ret_val = check_arguments(logger=logger)
    if ret_val != amc.E_SUCCESS:
        sys.exit(ret_val)

    # split gLABs out file in parts
    dglab_tmpfiles = glab_parser.split_glab_outfile(glab_outfile=amc.dRTK['glab_out'], logger=logger)

    # read in the OUTPUT messages from OUTPUT temp file
    glab_parser.parse_glab_info(glab_info=dglab_tmpfiles['INFO'], logger=logger)
    df_output = glab_parser.parse_glab_output(glab_output=dglab_tmpfiles['OUTPUT'], logger=logger)

    # plot the gLABs OUTPUT messages
    glab_plot_output.plot_glab_position(dfCrd=df_output, showplot=show_plot, logger=logger)

    # report to the user
    logger.info('{func:s}: amc.dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return amc.E_SUCCESS


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
