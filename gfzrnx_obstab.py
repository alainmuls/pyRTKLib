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


lst_logging_choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

lst_gnsss = ['E', 'G']

lst_e_markers = ['GALI', 'GPRS']
lst_g_markers = ['GPSN']

dMarkers = dict(zip(lst_gnsss, [lst_e_markers, lst_g_markers]))

lst_markers = list(set(lst_e_markers) | set(lst_g_markers))
lst_markers.sort()


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        for log_action in log_actions:
            if log_action not in lst_logging_choices:
                raise argparse.ArgumentError(self, "log_actions must be in {logoptions!s}".format(logoptions='|'.join(lst_logging_choices)))
        setattr(namespace, self.dest, log_actions)


def treatCmdOpts(argv: list):
    """
    Treats the command line options
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = baseName + ' creates and analyses the observation tabular file *.obstab from gfzrnx'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-d', '--dir_rnx', help='Directory with RINEX files (default {:s})'.format(colored('.', 'green')), required=False, type=str, default='.')

    parser.add_argument('-m', '--marker', help='marker name (4 chars, one of {markers:s}, default {marker:s})'.format(markers='|'.join(lst_markers), marker=colored(lst_markers[lst_markers.index('GALI')], 'green')), type=str, required=False, default=[lst_markers[lst_markers.index('GALI')]], action=marker_action)
    parser.add_argument('-p', '--prcodes', help='select from {prcodes:s} (default to {prcode:s})'.format(prcodes='|'.join(lst_prcodes), prcode=colored(lst_prcodes[lst_prcodes.index('C1C')], 'green')), required=False, type=str, default=lst_prcodes[lst_prcodes.index('C1C')], action=prcode_action, nargs='+')


    parser.add_argument('-c', '--cutoff', help='minimal cutoff angle (default 0 deg)', required=False, default=0, type=int, action=cutoff_action)
    parser.add_argument('-t', '--tmult', help='multiplier of nominal interval for gap detection', default=30, type=int, action=multiplier_action)

    parser.add_argument('-v', '--view_plots', help='view interactive plots (default True)', action='store_true', required=False, default=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (two of {choices:s}, default {choice:s})'.format(choices='|'.join(lst_logging_choices), choice=colored(' '.join(lst_logging_choices[3:5]), 'green')), nargs=2, required=False, default=lst_logging_choices[3:5], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.gnsss, args.prcodes, args.marker, args.cutoff, args.tmult, args.view_plots, args.logging


def main(argv):
    """
    pyconvbin converts raw data from SBF/UBlox to RINEX

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # store parameters
    amc.dRTK = {}
    cli_opt = {}

    # treat command line options
    cli_opt['rnx_dir'], cli_opt['gnsss'], cli_opt['prcodes'], cli_opt['marker'], cli_opt['cutoff'], cli_opt['tmult'], showPlots, logLevels = treatCmdOpts(argv)
    amc.dRTK['options'] = cli_opt

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=amc.dRTK['options']['rnx_dir'], logLevels=logLevels)

    logger.info('{func:s}: arguments processed: {args!s}'.format(args=amc.dRTK['options']['rnx_dir'], func=cFuncName))


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
