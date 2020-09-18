#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
import logging

import am_config as amc

__author__ = 'amuls'


lst_rxtype = ['ASTX', 'BEGP']
lst_logging_choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
dir_rinex_choices = [os.path.join(os.path.expanduser("~"), 'RxTURP/BEGPIOS/ASTX'), os.path.join(os.path.expanduser("~"), 'RxTURP/BEGPIOS/BEGP')]
dir_igs = os.path.join(os.path.expanduser("~"), 'RxTURP/BEGPIOS/igs')


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        for log_action in log_actions:
            if log_action not in lst_logging_choices:
                raise argparse.ArgumentError(self, "log_actions must be in {!s}".format('|',join(lst_logging_choices)))
        setattr(namespace, self.dest, log_actions)

class doy_action(argparse.Action):
    def __call__(self, parser, namespace, doy, option_string=None):
        if doy in range(start=1, end=366):
            raise argparse.ArgumentError(self, "day-of-year must be in [1...366]")
        setattr(namespace, self.dest, doy)


def treatCmdOpts(argv):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = amc.cBaseName + ' processes gLAB (v6) receiver position based on a template configuration file'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-r', '--rinexdir', help='Root RINEX directory (one of {choices:s} (default {choice:s}))'.format(choices='|'.join(dir_rinex_choices), choice=colored(dir_rinex_choices[0], 'green')), required=False, type=str, default='{:s}'.format(dir_rinex_choices[0]))
    parser.add_argument('-i', '--igsdir', help='Root IGS directory (default {:s})'.format(colored(dir_igs, 'green')), required=False, type=str, default='{:s}'.format(dir_igs))

    parser.add_argument('-y', '--year', help='Year (4 digits)', required=True, type=int)
    parser.add_argument('-d', '--doy', help='day-of-year [1..366]', required=True, type=int, action=doy_action)



    parser.add_argument('-l', '--logging', help='specify logging level console/file (two of {choices:s}, default {choice:s})'.format(choices='|'.join(lst_logging_choices), choice=colored(' '.join(lst_logging_choices[3:5]), 'green')), nargs=2, required=False, default=lst_logging_choices[3:5], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.rootdir, args.file, args.scale, args.center, args.db, args.plots, args.logging


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
    dir_root, glab_out, scale_enu, center_enu, db_cvs, show_plot, log_levels = treatCmdOpts(argv)

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=dir_root, logLevels=log_levels)


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
