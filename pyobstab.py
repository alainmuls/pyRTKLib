#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import logging

import am_config as amc
from gfzrnx import rnxobs_tabular
from ampyutils import amutils, location

__author__ = 'amuls'


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']
        for log_action in log_actions:
            if log_action not in choices:
                raise argparse.ArgumentError(self, "log_actions must be in {!s}".format(choices))
        setattr(namespace, self.dest, log_actions)


def treatCmdOpts(argv: list):
    """
    Treats the command line options
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = baseName + ' processes the observation tabular file *.obstab'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-d', '--dir', help='Directory for RINEX output (default {:s})'.format(colored('.', 'green')), required=False, type=str, default='.')
    parser.add_argument('-f', '--file', help='RINEX observation file', required=True, type=str)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.file, args.logging


def checkValidityArgs(logger: logging.Logger) -> bool:
    """
    checks for existence of dirs/files
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # change to baseDir, everything is relative to this directory
    logger.info('{func:s}: check existence of rinex dir {rnxd:s}'.format(func=cFuncName, rnxd=amc.dRTK['rnx_dir']))
    amc.dRTK['rnx_dir'] = os.path.expanduser(amc.dRTK['rnx_dir'])
    if not os.path.exists(amc.dRTK['rnx_dir']):
        logger.error('{func:s}   !!! Dir {basedir:s} does not exist.'.format(func=cFuncName, basedir=amc.dRTK['rnx_dir']))
        return amc.E_INVALID_ARGS

    # make the coplete filename by adding to rnx_dir and check existence of RINEX obs file to convert
    logger.info('{func:s}: check existence of RINEX observation file {rnx_obs:s}'.format(func=cFuncName, rnx_obs=os.path.join(amc.dRTK['rnx_dir'], amc.dRTK['rnx_obs'])))
    if not os.access(os.path.join(amc.dRTK['rnx_dir'], amc.dRTK['rnx_obs']), os.R_OK):
        logger.error('{func:s}   !!! RINEX observation file {rnx_obs:s} not accessible.'.format(func=cFuncName, rnx_obs=amc.dRTK['rnx_obs']))
        return amc.E_FILE_NOT_EXIST

    # check existence of rinexdir and create if needed
    logger.info('{func:s}: check existence of gfzrnx_dir {gfzrnx:s}'.format(func=cFuncName, gfzrnx=amc.dRTK['gfzrnx_dir']))
    if not os.path.exists(amc.dRTK['gfzrnx_dir']):
        logger.error('{func:s}   !!! Dir {basedir:s} does not exist.'.format(func=cFuncName, basedir=amc.dRTK['gfzrnx_dir']))
        return amc.E_DIR_NOT_EXIST

    return amc.E_SUCCESS


def main(argv):
    """
    pyconvbin converts raw data from SBF/UBlox to RINEX

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # treat command line options
    rnx_dir, rnx_obs, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger = amc.createLoggers(os.path.basename(__file__), dir=rnx_dir, logLevels=logLevels)

    # store cli parameters
    amc.dRTK = {}
    amc.dRTK['rnx_dir'] = rnx_dir
    amc.dRTK['rnx_obs'] = rnx_obs
    amc.dRTK['gfzrnx_dir'] = os.path.join(rnx_dir, 'gfzrnx')

    logger.info('{func:s}: arguments processed: amc.dRTK = {drtk!s}'.format(func=cFuncName, drtk=amc.dRTK))

    # check validity of passed arguments
    retCode = checkValidityArgs(logger=logger)
    if retCode != amc.E_SUCCESS:
        logger.error('{func:s}: Program exits with code {error:s}'.format(func=cFuncName, error=colored('{!s}'.format(retCode), 'red')))
        sys.exit(retCode)

    # locate the conversion programs SBF2RIN and CONVBIN
    amc.dRTK['bin'] = {}
    amc.dRTK['bin']['GFZRNX'] = location.locateProg('gfzrnx', logger)

    # get the header info from the observation file
    rnxobs_tabular.rnxobs_header_info(logger=logger)


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
