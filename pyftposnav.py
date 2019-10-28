#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
from json import encoder
import logging
import subprocess

from ampyutils import exeprogram, amutils, location
import am_config as amc

__author__ = 'amuls'


def treatCmdOpts(argv: list):
    """
    Treats the command line options
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')
    cFuncName = amc.cBaseName + ': ' + colored(sys._getframe().f_code.co_name, 'green')

    helpTxt = baseName + ' downloads  file from FTP server'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-r', '--rootdir', help="session's root directory (default {:s})".format(colored(amc.dRTK['local']['root'], 'green')), required=False, type=str, default='.')
    parser.add_argument('-s', '--server', help='FTP server (default {:s})'.format(colored(amc.dRTK['ftp']['server'], 'green')), required=False, type=str, default=amc.dRTK['ftp']['server'])
    parser.add_argument('-y', '--year', help='year (4 digits)', required=True, type=int)
    parser.add_argument('-d', '--doy', help='day of year', required=True, type=int)

    parser.add_argument('-o', '--overwrite', help='overwrite intermediate files (default {:s})'.format(colored('False', 'green')), action='store_true', required=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.rootdir, args.server, args.year, args.doy, args.overwrite, args.logging


def main(argv):
    """
    pyconvbin converts raw data from SBF/UBlox to RINEX

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # limit float precision
    encoder.FLOAT_REPR = lambda o: format(o, '.3f')

    # store parameters
    amc.dRTK = {}
    dFTP = {}
    dFTP['server'] = 'cddis.gsfc.nasa.gov'
    dFTP['user'] = 'ftp'
    dFTP['passwd'] = 'alain.muls@gmail.com'
    amc.dRTK['ftp'] = dFTP
    dDate = {}
    amc.dRTK['date'] = dDate
    dLocal = {}
    dLocal['root'] = '.'
    amc.dRTK['local'] = dLocal

    # treat command line options
    rootDir, amc.dRTK['ftp']['server'], dDate['year'], dDate['doy'], overwrite, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger = amc.createLoggers(os.path.basename(__file__), dir=rootDir, logLevels=logLevels)

    # create the directory and filename to download the combined RINEX file from

    # report to the user
    logger.info('{func:s}: amc.dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4)))


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
