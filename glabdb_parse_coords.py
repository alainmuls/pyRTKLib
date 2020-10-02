#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
import logging
import pathlib

import am_config as amc
from glab import glab_constants as glc
from glab import glab_parsedb
from ampyutils import amutils

lst_logging_choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

lst_gnsss = ['E', 'G', 'GE']
lst_prcodes = ['C1C', 'C1W', 'C2L', 'C2W', 'C2W', 'C5Q', 'C1A', 'C6A']

lst_markers = ['None', 'GALI', 'GPSN', 'COMB', 'GPRS']

glab_db = os.path.join(os.path.expanduser("~"), 'RxTURP/', 'glab_output_db.csv')


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        for log_action in log_actions:
            if log_action not in lst_logging_choices:
                raise argparse.ArgumentError(self, "log_actions must be in {logoptions!s}".format(logoptions='|'.join(lst_logging_choices)))
        setattr(namespace, self.dest, log_actions)


class gnss_action(argparse.Action):
    def __call__(self, parser, namespace, gnsss, option_string=None):
        for gnss in gnsss:
            if gnss not in lst_gnsss:
                raise argparse.ArgumentError(self, 'select GNSS(s) out of {gnsss:s}'.format(gnsss='|'.join(lst_gnsss)))
        setattr(namespace, self.dest, gnsss)


class prcode_action(argparse.Action):
    def __call__(self, parser, namespace, prcodes, option_string=None):
        for prcode in prcodes:
            if prcode not in lst_prcodes:
                raise argparse.ArgumentError(self, 'prcode is one of {prcodes:s}'.format(prcodes='|'.join(lst_prcodes)))
        setattr(namespace, self.dest, prcodes)


class doy_start_action(argparse.Action):
    def __call__(self, parser, namespace, doy, option_string=None):
        if doy not in range(1, 366):
            raise argparse.ArgumentError(self, "start day-of-year must be in [1...366]")
        setattr(namespace, self.dest, doy)


class doy_end_action(argparse.Action):
    def __call__(self, parser, namespace, doy, option_string=None):
        if doy not in range(1, 366):
            raise argparse.ArgumentError(self, "end day-of-year must be in [doy_start + 1...366]")
        setattr(namespace, self.dest, doy)


class marker_action(argparse.Action):
    def __call__(self, parser, namespace, markers, option_string=None):
        for marker in markers:
            if marker not in lst_markers:
                raise argparse.ArgumentError(self, 'marker is one of {markers:s}'.format(markers='|'.join(lst_markers)))
        setattr(namespace, self.dest, markers)


def treatCmdOpts(argv):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = amc.cBaseName + ' creates overview of position results for GNSS / codes'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)

    parser.add_argument('-d', '--dbglab', help='glab CSV dbase file (default {glabdb:s})'.format(glabdb=colored(glab_db, 'green')), required=False, type=str, default=glab_db)

    parser.add_argument('-g', '--gnsss', help='select GNSS(s) to use (out of {gnsss:s}, default {gnss:s})'.format(gnsss='|'.join(lst_gnsss), gnss=colored(lst_gnsss[0], 'green')), default=lst_gnsss[0], type=str, required=False, action=gnss_action, nargs='+')
    parser.add_argument('-p', '--prcodes', help='select from {prcodes:s} (default to {prcode:s})'.format(prcodes='|'.join(lst_prcodes), prcode=colored(lst_prcodes[0], 'green')), required=False, type=str, default=lst_prcodes[0], action=prcode_action, nargs='+')
    parser.add_argument('-m', '--marker', help='marker name (4 chars, one of {markers:s}, default {marker:s})'.format(markers='|'.join(lst_markers), marker=colored(lst_markers[0], 'green')), type=str, required=False, default=[lst_markers[0]], action=marker_action, nargs='+')

    parser.add_argument('-y', '--year', help='Year (4 digits)', required=True, type=int)
    parser.add_argument('-s', '--doy_start', help='start day-of-year [1..366]', required=True, type=int, action=doy_start_action)
    parser.add_argument('-e', '--doy_end', help='end day-of-year [doy_start + 1..366]', required=True, type=int, action=doy_end_action)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (two of {choices:s}, default {choice:s})'.format(choices='|'.join(lst_logging_choices), choice=colored(' '.join(lst_logging_choices[3:5]), 'green')), nargs=2, required=False, default=lst_logging_choices[3:5], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dbglab, args.gnsss, args.prcodes, args.marker, args.year, args.doy_start, args.doy_end, args.logging


def check_arguments(logger: logging.Logger) -> int:
    """
    check_arguments checks the given arguments wether they are valid. return True or False
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # check whether doy_last is after doy_start
    if amc.dRTK['options']['doy_begin'] > amc.dRTK['options']['doy_last']:
        logger.info('{func:s} "end day-of-year" ({end:d}) must be at least "begin day-of-year" ({start:d})'.format(end=amc.dRTK['options']['doy_last'], start=amc.dRTK['options']['doy_begin'], func=cFuncName))
        return amc.E_INVALID_ARGS

    # check existence of glab db CSV file
    path = pathlib.Path(amc.dRTK['options']['glab_db'])
    if not path.is_file():
        logger.info('{func:s}: gLAB CSV database file {csv:s} does not exist'.format(csv=colored(amc.dRTK['options']['glab_db'], 'red'), func=cFuncName))
        return amc.E_FILE_NOT_EXIST

    return amc.E_SUCCESS


def main(argv) -> bool:
    """
    glabplotposn plots data from gLAB (v6) OUTPUT messages

    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # store cli parameters
    amc.dRTK = {}
    cli_opt = {}
    cli_opt['glab_db'], cli_opt['gnsss'], cli_opt['prcodes'], cli_opt['markers'], cli_opt['yyyy'], cli_opt['doy_begin'], cli_opt['doy_last'], log_levels = treatCmdOpts(argv)
    amc.dRTK['options'] = cli_opt

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=os.getcwd(), logLevels=log_levels)

    # check  arguments
    ret_val = check_arguments(logger=logger)
    if ret_val != amc.E_SUCCESS:
        sys.exit(ret_val)

    # parse the database file to get the GNSSs and prcodes we need
    glab_parsedb.db_parse_gnss_codes(db_name=amc.dRTK['options']['glab_db'], crd_types=glc.dgLab['OUTPUT']['ENU'], logger=logger)

    # report to the user
    logger.info('{func:s}: Project information =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return amc.E_SUCCESS


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
