#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
from json import encoder
import logging
import subprocess
import tempfile

from ampyutils import amutils, location
import am_config as amc

__author__ = 'amuls'


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
    parser.add_argument('-b', '--binary', help='Select binary format (default {:s})'.format(colored('SBF', 'green')), required=False, type=str, choices=['SBF', 'UBlox'], default='SBF')
    parser.add_argument('-r', '--rinexdir', help='Directory for RINEX output (default {:s})'.format(colored('.', 'green')), required=False, type=str, default='.')
    parser.add_argument('-g', '--gnss', help='GNSS systems to process (default={:s})'.format(colored('gal', 'green')), required=False, default='gal', choices=['gal', 'gps', 'com'])
    parser.add_argument('-n', '--naming', help='Enter MARKER DOY YY for naming RINEX output files', nargs=3, required=True)
    # parser.add_argument('-c', '--convfile', help='Converted name of RINEX file (default named by converter program)', required=False, default=None)

    parser.add_argument('-o', '--overwrite', help='overwrite intermediate files (default {:s})'.format(colored('False', 'green')), action='store_true', required=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.file, args.binary, args.rinexdir, args.gnss, args.naming, args.overwrite, args.logging


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
    amc.dRTK['binFile'] = os.path.join(amc.dRTK['rootDir'], amc.dRTK['binFile'])
    logger.info('{func:s}: check existence of binary file {bin:s} to convert'.format(func=cFuncName, bin=amc.dRTK['binFile']))
    if not os.access(amc.dRTK['binFile'], os.R_OK):
        logger.error('{func:s}   !!! binary observation file {bin:s} not accessible.'.format(func=cFuncName, bin=amc.dRTK['binFile']))
        return amc.E_FILE_NOT_EXIST

    # check existence of rinexdir and create if needed
    logger.info('{func:s}: check existence of rinexdir {rinex:s} and create if needed'.format(func=cFuncName, rinex=amc.dRTK['rinexDir']))
    # amc.dRTK['rinexDir'] = os.path.join(amc.dRTK['rootDir'], amc.dRTK['rinexDir'])
    amutils.mkdir_p(amc.dRTK['rinexDir'])

    # check whether the rinexNaming arguments are correctly formatted
    amc.dRTK['marker'] = amc.dRTK['rinexNaming'][0]
    amc.dRTK['doy'] = amc.dRTK['rinexNaming'][1]
    amc.dRTK['yy'] = amc.dRTK['rinexNaming'][2]

    if (len(amc.dRTK['marker']) < 4) or (len(amc.dRTK['doy']) != 3) or (len(amc.dRTK['yy']) != 2):
        logger.error('{func:s}: Please enter rinexNaming as follows'.format(func=cFuncName))
        logger.error('{func:s}: ... marker {marker:s} at least 4 chars'.format(func=cFuncName, marker=amc.dRTK['marker']))
        logger.error('{func:s}: ... doy {doy:s} exact 3 chars'.format(func=cFuncName, doy=amc.dRTK['doy']))
        logger.error('{func:s}: ... yy {yy:s} exact 2   chars'.format(func=cFuncName, yy=amc.dRTK['yy']))
        return amc.E_INVALID_ARGS

    return amc.E_SUCCESS


def run_subprocess(sub_proc: list, logger: logging.Logger):
    """
    run_subprocess runs the program with arguments in the sub_proc list
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    try:
        print('running {:s}'.format(sub_proc[0]))
        subprocess.check_call(sub_proc)
    except subprocess.CalledProcessError as e:
        # handle errors in the called executable
        logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=sub_proc[0], err=e))
        sys.exit(amc.E_SBF2RIN_ERRCODE)
    except OSError as e:
        # executable not found
        logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=sub_proc[0], err=e))
        sys.exit(amc.E_OSERROR)


def sbf2rinex(dGnssSysts: dict, logger: logging.Logger):
    """
    sbf2rinex converts a SBF file to rinex according to the GNSS systems selected
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # convert to RINEX for selected GNSS system
    logger.info('{func:s}: RINEX conversion for {gnss:s}'.format(func=cFuncName, gnss=colored(amc.dRTK['gnssSyst'], 'green')))

    # determine systems to exclude, adjust when COM is asked meaning use GAL+GPS
    typeNav = 'P'
    excludeGNSSs = 'RSCJI'
    # if amc.dRTK['gnssSyst'].lower() == 'com':
    #     excludeGNSSs = [key for key, value in dGnssSysts.items() if not (value.lower().startswith('gal') or value.lower().startswith('gps'))]
    #     typeNav = 'P'
    # else:
    #     excludeGNSSs = [key for key, value in dGnssSysts.items() if not value.lower().startswith(amc.dRTK['gnssSyst'].lower())]
    #     if amc.dRTK['gnssSyst'].lower() == 'gps':
    #         typeNav = 'N'
    #     elif amc.dRTK['gnssSyst'].lower() == 'gal':
    #         typeNav = 'E'

    logger.info('{func:s}: excluding GNSS systems {excl!s}'.format(func=cFuncName, excl=excludeGNSSs))

    # convert to RINEX observables file
    args4SBF2RIN = [amc.dRTK['bin2rnx']['SBF2RIN'], '-f', amc.dRTK['binFile'], '-x', excludeGNSSs, '-s', '-D', '-v', '-R3']

    # create the output RINEX obs file name
    amc.dRTK['obs'] = '{marker:s}{doy:s}0.{yy:s}O'.format(marker=amc.dRTK['marker'], doy=amc.dRTK['doy'], yy=amc.dRTK['yy'])
    amc.dRTK['obs_full'] = os.path.join(amc.dRTK['rinexDir'], amc.dRTK['obs'])
    # args4SBF2RIN.extend(['-o', amc.dRTK['obs']])
    args4SBF2RIN.extend(['-o', os.path.join(tempfile.gettempdir(), amc.dRTK['obs'])])

    logger.info('{func:s}: creating RINEX observation file\n{opts!s}'.format(func=cFuncName, opts=' '.join(args4SBF2RIN)))

    # run the sbf2rin program
    run_subprocess(sub_proc=args4SBF2RIN, logger=logger)

    # convert to RINEX NAVIGATION file
    args4SBF2RIN = [amc.dRTK['bin2rnx']['SBF2RIN'], '-f', amc.dRTK['binFile'], '-x', excludeGNSSs, '-s', '-D', '-v', '-n', typeNav, '-R3']

    # create the output RINEX obs file name
    amc.dRTK['nav'] = '{marker:s}{doy:s}0.{yy:s}{typenav:s}'.format(marker=amc.dRTK['marker'], doy=amc.dRTK['doy'], yy=amc.dRTK['yy'], typenav=typeNav)
    amc.dRTK['nav_full'] = os.path.join(amc.dRTK['rinexDir'], amc.dRTK['nav'])
    # args4SBF2RIN.extend(['-o', amc.dRTK['nav']])
    args4SBF2RIN.extend(['-o', os.path.join(tempfile.gettempdir(), amc.dRTK['nav'])])

    logger.info('{func:s}: creating RINEX navigation file\n{opts!s}'.format(func=cFuncName, opts=' '.join(args4SBF2RIN)))

    # run the sbf2rin program
    run_subprocess(sub_proc=args4SBF2RIN, logger=logger)

    pass


def ubx2rinex(logger: logging.Logger):
    """
    UBX2rinex converts a UBX file to rinex according to the GNSS systems selected
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # convert to RINEX for selected GNSS system
    logger.info('{func:s}: RINEX conversion for {gnss:s}'.format(func=cFuncName, gnss=amc.dRTK['gnssSyst']))

    # dictionary of GNSS systems
    dGNSSSysts = {'G': 'GPS', 'R': 'GLO', 'E': 'GAL', 'S': 'SBS', 'C': 'BDS', 'J': 'QZS', 'I': 'IRN'}

    # determine systems to exclude, adjust when COM is asked meaning use GAL+GPS
    typeNav = ''
    if amc.dRTK['gnssSyst'].lower() == 'com':
        excludeGNSSs = [key for key, value in dGNSSSysts.items() if not (value.lower().startswith('gal') or value.lower().startswith('gps'))]
    else:
        excludeGNSSs = [key for key, value in dGNSSSysts.items() if not value.lower().startswith(amc.dRTK['gnssSyst'].lower())]
        if amc.dRTK['gnssSyst'].lower() == 'gps':
            typeNav = 'N'
        elif amc.dRTK['gnssSyst'].lower() == 'gal':
            typeNav = 'E'

    logger.info('{func:s}: excluding GNSS systems {excl!s}'.format(func=cFuncName, excl=excludeGNSSs))

    # convert to RINEX observables file
    args4UBX2RIN = [amc.dRTK['bin2rnx']['UBX2RIN'], 'file', amc.dRTK['binFile'], '-os', '-od']

    for deniedGNSS in excludeGNSSs:
        print(deniedGNSS)
        args4UBX2RIN.extend(['-y', deniedGNSS])

    print(args4UBX2RIN)

    # if amc.dRTK['rinexVersion'] == 'R3':
    #     args4UBX2RIN.extend(['-v', '3.01'])
    # else:
    #     args4UBX2RIN.extend(['-v', '2.11'])

    # create the output RINEX obs file name
    amc.dRTK['obs'] = '{marker:s}{doy:s}0.{yy:s}O'.format(marker=amc.dRTK['marker'], doy=amc.dRTK['doy'], yy=amc.dRTK['yy'])
    amc.dRTK['obs'] = os.path.join(amc.dRTK['rinexDir'], amc.dRTK['obs'])
    args4UBX2RIN.extend(['-o', amc.dRTK['obs']])

    logger.info('{func:s}: creating RINEX observation file\n{opts!s}'.format(func=cFuncName, opts=' '.join(args4UBX2RIN)))

    # run the ubx2rin program
    try:
        subprocess.check_call(args4UBX2RIN)
    except subprocess.CalledProcessError as e:
        # handle errors in the called executable
        logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=amc.dRTK['bin2rnx']['UBX2RIN'], err=e))
        sys.exit(amc.E_UBX2RIN_ERRCODE)
    except OSError as e:
        # executable not found
        logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=amc.dRTK['bin2rnx']['UBX2RIN'], err=e))
        sys.exit(amc.E_OSERROR)

    # convert to RINEX NAVIGATION file
    args4UBX2RIN = [amc.dRTK['bin2rnx']['UBX2RIN'], 'file', amc.dRTK['binFile'], '-os', '-od', '-n', typeNav]

    print(args4UBX2RIN)

    # if amc.dRTK['rinexVersion'] == 'R3':
    #     args4UBX2RIN.extend(['-v', '3.01'])
    # else:
    #     args4UBX2RIN.extend(['-v', '2.11'])

    # create the output RINEX obs file name
    print(typeNav)
    amc.dRTK['nav'] = '{marker:s}{doy:s}0.{yy:s}{typenav:s}'.format(marker=amc.dRTK['marker'], doy=amc.dRTK['doy'], yy=amc.dRTK['yy'], typenav=typeNav)
    amc.dRTK['nav'] = os.path.join(amc.dRTK['rinexDir'], amc.dRTK['nav'])
    args4UBX2RIN.extend(['-n', amc.dRTK['nav']])

    for deniedGNSS in excludeGNSSs:
        print(deniedGNSS)
        args4UBX2RIN.extend(['-y', deniedGNSS])

    # logger.info('{func:s}: creating RINEX navigation file\n{opts!s}'.format(func=cFuncName, opts=' '.join(args4UBX2RIN)))

    # run the ubx2rin program
    try:
        subprocess.check_call(args4UBX2RIN)
    except subprocess.CalledProcessError as e:
        # handle errors in the called executable
        logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=amc.dRTK['bin2rnx']['UBX2RIN'], err=e))
        sys.exit(amc.E_UBX2RIN_ERRCODE)
    except OSError as e:
        # executable not found
        logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=amc.dRTK['bin2rnx']['UBX2RIN'], err=e))
        sys.exit(amc.E_OSERROR)

    pass


# def ublox2rinex(logger: logging.Logger, dGnssSysts: dict):
#     """
#     ublox2rinex converts a uBLOX file to rinex according to the GNSS systems selected
#     """
#     cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

#     # convert to RINEX for selected GNSS system
#     logger.info('{func:s}: RINEX conversion for {gnss:s}'.format(func=cFuncName, gnss=amc.dRTK['gnssSyst']))

#     # determine systems to exclude, adjust when COM is asked meaning use GAL+GPS
#     if amc.dRTK['gnssSyst'].lower() == 'com':
#         excludeGNSSs = [key for key, value in dGnssSysts.items() if not (value.lower().startswith('gal') or value.lower().startswith('gps'))]
#     else:
#         excludeGNSSs = [key for key, value in dGnssSysts.items() if not value.lower().startswith(amc.dRTK['gnssSyst'].lower())]

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

    # dictionary of GNSS systems
    dGNSSSysts = {'G': 'GPS', 'R': 'Glonass', 'E': 'Galileo', 'S': 'SBAS', 'C': 'Beidou', 'J': 'QZSS', 'I': 'IRNSS'}

    # treat command line options
    rootDir, binFile, binType, rinexDir, gnssSyst, rinexNaming, overwrite, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger = amc.createLoggers(os.path.basename(__file__), dir=rootDir, logLevels=logLevels)

    # store cli parameters
    amc.dRTK = {}
    amc.dRTK['rootDir'] = rootDir
    amc.dRTK['binFile'] = binFile
    amc.dRTK['binType'] = binType
    amc.dRTK['rinexDir'] = rinexDir
    amc.dRTK['gnssSyst'] = gnssSyst
    amc.dRTK['rinexNaming'] = rinexNaming

    logger.info('{func:s}: arguments processed: amc.dRTK = {drtk!s}'.format(func=cFuncName, drtk=amc.dRTK))

    # check validity of passed arguments
    retCode = checkValidityArgs(logger=logger)
    if retCode != amc.E_SUCCESS:
        logger.error('{func:s}: Program exits with code {error:s}'.format(func=cFuncName, error=colored('{!s}'.format(retCode), 'red')))
        sys.exit(retCode)

    # locate the conversion programs SBF2RIN and CONVBIN
    amc.dRTK['bin2rnx'] = {}
    amc.dRTK['bin2rnx']['CONVBIN'] = location.locateProg('convbin', logger)
    amc.dRTK['bin2rnx']['SBF2RIN'] = location.locateProg('sbf2rin', logger)
    amc.dRTK['bin2rnx']['GFZRNX'] = location.locateProg('gfzrnx', logger)

    # convert binary file to rinex
    logger.info('{func:s}: convert binary file to rinex'.format(func=cFuncName))
    if amc.dRTK['binType'] == 'SBF':
        sbf2rinex(dGnssSysts=dGNSSSysts, logger=logger)
    else:
        ubx2rinex(dGnssSysts=dGNSSSysts, logger=logger)

    # report to the user
    logger.info('{func:s}: amc.dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4)))


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
