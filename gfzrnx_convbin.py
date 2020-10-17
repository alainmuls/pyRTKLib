#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
from json import encoder
import logging
import tempfile
from shutil import copyfile

from ampyutils import amutils, location
import am_config as amc
from gfzrnx import gfzrnx_ops

__author__ = 'amuls'


class interval_action(argparse.Action):
    def __call__(self, parser, namespace, interval, option_string=None):
        if not 5 <= int(interval) <= 60:
            raise argparse.ArgumentError(self, "interval must be in 5..60 minutes")
        setattr(namespace, self.dest, interval)


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

    helpTxt = baseName + ' convert binary raw data from SBF or UBlox to RINEX Obs & Nav files'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-d', '--dir', help='Root directory (default {:s})'.format(colored('.', 'green')), required=False, type=str, default='.')
    parser.add_argument('-f', '--file', help='Binary SBF or UBlox file', required=True, type=str)

    parser.add_argument('-b', '--binary', help='Select binary format (default {:s})'.format(colored('SBF', 'green')), required=False, type=str, choices=['SBF', 'UBX'], default='SBF')

    parser.add_argument('-r', '--rinexdir', help='Directory for RINEX output (default {:s})'.format(colored('.', 'green')), required=False, type=str, default='.')

    parser.add_argument('-c', '--cart', help='cartesian coordinates of antenna (default RMA)', required=False, type=float, nargs=3, default=[4023741.3045, 309110.4584, 4922723.1945])

    # parser.add_argument('-i', '--interval', help='interval for ASCII display of SVs ([5..60] minutes)', default=10, type=int, required=False, action=interval_action)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.file, args.binary, args.rinexdir, args.cart, args.logging


def checkValidityArgs(logger: logging.Logger) -> bool:
    """
    checks for existence of dirs/files
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # change to baseDir, everything is relative to this directory
    logger.info('{func:s}: check existence of rootDir {root:s}'.format(func=cFuncName, root=amc.dRTK['rootDir']))
    amc.dRTK['rootDir'] = os.path.expanduser(amc.dRTK['rootDir'])
    if not os.path.exists(amc.dRTK['rootDir']):
        logger.error('{func:s}   !!! Dir {basedir:s} does not exist.'.format(func=cFuncName, basedir=amc.dRTK['rootDir']))
        return amc.E_INVALID_ARGS

    # make the coplete filename by adding to rootdir and check existence of binary file to convert
    logger.info('{func:s}: check existence of binary file {bin:s} to convert'.format(func=cFuncName, bin=os.path.join(amc.dRTK['rootDir'], amc.dRTK['binFile'])))
    if not os.access(os.path.join(amc.dRTK['rootDir'], amc.dRTK['binFile']), os.R_OK):
        logger.error('{func:s}   !!! binary observation file {bin:s} not accessible.'.format(func=cFuncName, bin=amc.dRTK['binFile']))
        return amc.E_FILE_NOT_EXIST

    # check existence of rinexdir and create if needed
    logger.info('{func:s}: check existence of rinexdir {rinex:s} and create if needed'.format(func=cFuncName, rinex=amc.dRTK['rinexDir']))
    amutils.mkdir_p(amc.dRTK['rinexDir'])

    # check existence of rinexdir and create if needed
    logger.info('{func:s}: check existence of gfzrnxdir {gfzrnx:s} and create if needed'.format(func=cFuncName, gfzrnx=amc.dRTK['gfzrnxDir']))
    amutils.mkdir_p(amc.dRTK['gfzrnxDir'])

    return amc.E_SUCCESS


def sbf2rinex(logger: logging.Logger) -> dict:
    """
    sbf2rinex converts a SBF file to rinex according to the GNSS systems selected
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # convert to RINEX for selected GNSS system
    logger.info('{func:s}: RINEX conversion from SBF binary'.format(func=cFuncName))

    # we'll convert always by for only GPS & Galileo, excluding other GNSSs
    excludeGNSSs = 'RSCJI'

    # dict with the name of the temporary created RINEX obs/nav files for later checking by GFZRNX
    dTmpRnx = {}

    # convert to RINEX observable file
    args4SBF2RIN = [amc.dRTK['bin']['SBF2RIN'], '-f', os.path.join(amc.dRTK['rootDir'], amc.dRTK['binFile']), '-x', excludeGNSSs, '-s', '-D', '-v', '-R3']
    # create the output RINEX obs file name
    dTmpRnx['obs'] = os.path.join(tempfile.gettempdir(), tempfile.NamedTemporaryFile(prefix="COMB_", suffix=".obs").name)
    args4SBF2RIN.extend(['-o', dTmpRnx['obs']])

    # run the sbf2rin program
    logger.info('{func:s}: creating RINEX observation file'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4SBF2RIN, logger=logger)

    # convert to RINEX NAVIGATION file
    args4SBF2RIN = [amc.dRTK['bin']['SBF2RIN'], '-f', os.path.join(amc.dRTK['rootDir'], amc.dRTK['binFile']), '-x', excludeGNSSs, '-s', '-D', '-v', '-n', 'P', '-R3']
    # create the output RINEX obs file name
    dTmpRnx['nav'] = os.path.join(tempfile.gettempdir(), tempfile.NamedTemporaryFile(prefix="COMB_", suffix=".nav").name)
    args4SBF2RIN.extend(['-o', dTmpRnx['nav']])

    # run the sbf2rin program
    logger.info('{func:s}: creating RINEX navigation file'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4SBF2RIN, logger=logger)

    return dTmpRnx


def ubx2rinex(logger: logging.Logger):
    """
    UBX2rinex converts a UBX file to rinex according to the GNSS systems selected
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # # convert to RINEX for selected GNSS system
    # logger.info('{func:s}: RINEX conversion for {gnss:s}'.format(func=cFuncName, gnss=amc.dRTK['gnssSyst']))

    # # dictionary of GNSS systems
    # amc.dGNSSs = {'G': 'GPS', 'R': 'GLO', 'E': 'GAL', 'S': 'SBS', 'C': 'BDS', 'J': 'QZS', 'I': 'IRN'}

    # # determine systems to exclude, adjust when COM is asked meaning use GAL+GPS
    # typeNav = ''
    # if amc.dRTK['gnssSyst'].lower() == 'com':
    #     excludeGNSSs = [key for key, value in amc.dGNSSs.items() if not (value.lower().startswith('gal') or value.lower().startswith('gps'))]
    # else:
    #     excludeGNSSs = [key for key, value in amc.dGNSSs.items() if not value.lower().startswith(amc.dRTK['gnssSyst'].lower())]
    #     if amc.dRTK['gnssSyst'].lower() == 'gps':
    #         typeNav = 'N'
    #     elif amc.dRTK['gnssSyst'].lower() == 'gal':
    #         typeNav = 'E'

    # logger.info('{func:s}: excluding GNSS systems {excl!s}'.format(func=cFuncName, excl=excludeGNSSs))

    # # convert to RINEX observables file
    # args4UBX2RIN = [amc.dRTK['bin']['UBX2RIN'], 'file', amc.dRTK['binFile'], '-os', '-od']

    # for deniedGNSS in excludeGNSSs:
    #     print(deniedGNSS)
    #     args4UBX2RIN.extend(['-y', deniedGNSS])

    # print(args4UBX2RIN)

    # # if amc.dRTK['rinexVersion'] == 'R3':
    # #     args4UBX2RIN.extend(['-v', '3.01'])
    # # else:
    # #     args4UBX2RIN.extend(['-v', '2.11'])

    # # create the output RINEX obs file name
    # amc.dRTK['obs'] = '{marker:s}{doy:s}0.{yy:s}O'.format(marker=amc.dRTK['marker'], doy=amc.dRTK['DoY'], yy=amc.dRTK['yy'])
    # amc.dRTK['obs'] = os.path.join(amc.dRTK['rinexDir'], amc.dRTK['obs'])
    # args4UBX2RIN.extend(['-o', amc.dRTK['obs']])

    # logger.info('{func:s}: creating RINEX observation file\n{opts!s}'.format(func=cFuncName, opts=' '.join(args4UBX2RIN)))

    # # run the ubx2rin program
    # try:
    #     subprocess.check_call(args4UBX2RIN)
    # except subprocess.CalledProcessError as e:
    #     # handle errors in the called executable
    #     logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=amc.dRTK['bin']['UBX2RIN'], err=e))
    #     sys.exit(amc.E_UBX2RIN_ERRCODE)
    # except OSError as e:
    #     # executable not found
    #     logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=amc.dRTK['bin']['UBX2RIN'], err=e))
    #     sys.exit(amc.E_OSERROR)

    # # convert to RINEX NAVIGATION file
    # args4UBX2RIN = [amc.dRTK['bin']['UBX2RIN'], 'file', amc.dRTK['binFile'], '-os', '-od', '-n', typeNav]

    # print(args4UBX2RIN)

    # # if amc.dRTK['rinexVersion'] == 'R3':
    # #     args4UBX2RIN.extend(['-v', '3.01'])
    # # else:
    # #     args4UBX2RIN.extend(['-v', '2.11'])

    # # create the output RINEX obs file name
    # print(typeNav)
    # amc.dRTK['nav'] = '{marker:s}{doy:s}0.{yy:s}{typenav:s}'.format(marker=amc.dRTK['marker'], doy=amc.dRTK['DoY'], yy=amc.dRTK['yy'], typenav=typeNav)
    # amc.dRTK['nav'] = os.path.join(amc.dRTK['rinexDir'], amc.dRTK['nav'])
    # args4UBX2RIN.extend(['-n', amc.dRTK['nav']])

    # for deniedGNSS in excludeGNSSs:
    #     print(deniedGNSS)
    #     args4UBX2RIN.extend(['-y', deniedGNSS])

    # # logger.info('{func:s}: creating RINEX navigation file\n{opts!s}'.format(func=cFuncName, opts=' '.join(args4UBX2RIN)))

    # # run the ubx2rin program
    # try:
    #     subprocess.check_call(args4UBX2RIN)
    # except subprocess.CalledProcessError as e:
    #     # handle errors in the called executable
    #     logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=amc.dRTK['bin']['UBX2RIN'], err=e))
    #     sys.exit(amc.E_UBX2RIN_ERRCODE)
    # except OSError as e:
    #     # executable not found
    #     logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=amc.dRTK['bin']['UBX2RIN'], err=e))
    #     sys.exit(amc.E_OSERROR)

    pass


# def ublox2rinex(logger: logging.Logger, amc.dGNSSs: dict):
#     """
#     ublox2rinex converts a uBLOX file to rinex according to the GNSS systems selected
#     """
#     cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

#     # convert to RINEX for selected GNSS system
#     logger.info('{func:s}: RINEX conversion for {gnss:s}'.format(func=cFuncName, gnss=amc.dRTK['gnssSyst']))

#     # determine systems to exclude, adjust when COM is asked meaning use GAL+GPS
#     if amc.dRTK['gnssSyst'].lower() == 'com':
#         excludeGNSSs = [key for key, value in amc.dGNSSs.items() if not (value.lower().startswith('gal') or value.lower().startswith('gps'))]
#     else:
#         excludeGNSSs = [key for key, value in amc.dGNSSs.items() if not value.lower().startswith(amc.dRTK['gnssSyst'].lower())]

#     logger.info('{func:s}: excluding GNSS systems {excl!s}'.format(func=cFuncName, excl=excludeGNSSs))

#     pass


def main(argv):
    """
    pyconvbin converts raw data from SBF/UBlox to RINEX

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # limit float precision
    encoder.FLOAT_REPR = lambda o: format(o, '.3f')

    # treat command line options
    rootDir, binFile, binType, rinexDir, crd_cart, interval, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=rootDir, logLevels=logLevels)

    # store cli parameters
    amc.dRTK = {}
    amc.dRTK['rootDir'] = rootDir
    amc.dRTK['binFile'] = binFile
    amc.dRTK['binType'] = binType
    amc.dRTK['rinexDir'] = rinexDir
    amc.dRTK['ant_crds'] = crd_cart
    amc.dRTK['interval'] = interval * 60
    amc.dRTK['gfzrnxDir'] = os.path.join(rinexDir, 'gfzrnx')

    logger.info('{func:s}: arguments processed: amc.dRTK = {drtk!s}'.format(func=cFuncName, drtk=amc.dRTK))

    # check validity of passed arguments
    retCode = checkValidityArgs(logger=logger)
    if retCode != amc.E_SUCCESS:
        logger.error('{func:s}: Program exits with code {error:s}'.format(func=cFuncName, error=colored('{!s}'.format(retCode), 'red')))
        sys.exit(retCode)

    # locate the conversion programs SBF2RIN and CONVBIN
    amc.dRTK['bin'] = {}
    amc.dRTK['bin']['CONVBIN'] = location.locateProg('convbin', logger)
    amc.dRTK['bin']['SBF2RIN'] = location.locateProg('sbf2rin', logger)
    amc.dRTK['bin']['GFZRNX'] = location.locateProg('gfzrnx', logger)
    amc.dRTK['bin']['RNX2CRZ'] = location.locateProg('rnx2crz', logger)
    amc.dRTK['bin']['COMPRESS'] = location.locateProg('compress', logger)
    amc.dRTK['bin']['GZIP'] = location.locateProg('gzip', logger)

    # convert binary file to rinex
    if amc.dRTK['binType'] == 'SBF':
        logger.info('{func:s}: convert binary file to rinex'.format(func=cFuncName))
        dRnxTmp = sbf2rinex(logger=logger)
        logger.info('{func:s}: extracting RINEX header info'.format(func=cFuncName))
        gfzrnx_ops.rnxobs_header_info(dTmpRnx=dRnxTmp, logger=logger)
        # gfzrnx_ops.rnxobs_statistics_file(dTmpRnx=dRnxTmp, logger=logger)
        logger.info('{func:s}: creeate RINEX files in rinex/YYDOY location'.format(func=cFuncName))
        gfzrnx_ops.gnss_rinex_creation(dTmpRnx=dRnxTmp, logger=logger)
        logger.info('{func:s}: compressing files'.format(func=cFuncName))
        gfzrnx_ops.compress_rinex_obsnav(logger=logger)
    else:
        ubx2rinex(logger=logger)

    # report to the user
    logger.info('{func:s}: amc.dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))
    # store the json structure
    jsonName = os.path.join(amc.dRTK['rinexDir'], amc.dRTK['binFile'].replace('.', '-') + '.json')
    with open(jsonName, 'w') as f:
        json.dump(amc.dRTK, f, ensure_ascii=False, indent=4, default=amutils.DT_convertor)

    # remove the temporar files
    for fname in dRnxTmp.values():
        if os.path.isfile(fname):
            os.remove(fname)

    # copy temp log file to the YYDOY directory
    copyfile(log_name, os.path.join(amc.dRTK['rinexDir'], 'pyconvbin.log'))
    os.remove(log_name)


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
