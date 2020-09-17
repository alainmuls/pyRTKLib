#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
from json import encoder
import logging
from shutil import copyfile

import am_config as amc
from ampyutils import location, amutils, exeprogram

__author__ = 'amuls'


def treatCmdOpts(argv: list):
    """
    Treats the command line options
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = baseName + ' downloads  file from FTP server'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-r', '--rootdir', help="session's root directory (default {:s})".format(colored(amc.dRTK['local']['root'], 'green')), required=False, type=str, default='.')
    parser.add_argument('-s', '--server', help='FTP server (default {:s})'.format(colored(amc.dRTK['ftp']['server'], 'green')), required=False, type=str, default=amc.dRTK['ftp']['server'])
    parser.add_argument('-y', '--year', help='year (4 digits)', required=True, type=str)
    parser.add_argument('-d', '--doy', help='day of year', required=True, type=int)

    parser.add_argument('-o', '--overwrite', help='overwrite intermediate files (default {:s})'.format(colored('False', 'green')), action='store_true', required=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.rootdir, args.server, args.year, args.doy, args.overwrite, args.logging


def createRemoteFTPInfo(logger: logging.Logger) -> dict:
    """
    createRemoteFTPInfo creates the remote paths and files to download the RINEX navigation files for GAL, GPS and COM
    """
    dRemote = {}
    dGal = {}
    dGal['rpath'] = 'pub/gps/data/daily/{year:4s}/{DOY:3s}/{YY:2s}l'.format(year=str(amc.dRTK['date']['year']), DOY=amc.dRTK['date']['DoY'], YY=amc.dRTK['date']['YY'])
    dGal['rfile'] = 'BRUX00BEL_R_{year:4s}{DOY:s}0000_01D_EN.rnx.gz'.format(year=str(amc.dRTK['date']['year']), DOY=amc.dRTK['date']['DoY'])

    dGPS = {}
    dGPS['rpath'] = 'pub/gps/data/daily/{year:4s}/{DOY:3s}/{YY:2s}n'.format(year=str(amc.dRTK['date']['year']), DOY=amc.dRTK['date']['DoY'], YY=amc.dRTK['date']['YY'])
    # dGPS['rfile'] = 'brdc{DOY:3s}0.{YY:2s}n.Z'.format(DOY=amc.dRTK['date']['DoY'], YY=amc.dRTK['date']['YY'])
    dGPS['rfile'] = 'BRUX00BEL_R_{year:4s}{DOY:s}0000_01D_GN.rnx.gz'.format(year=str(amc.dRTK['date']['year']), DOY=amc.dRTK['date']['DoY'])

    dCom = {}
    dCom['rpath'] = 'pub/gps/data/daily/{year:4s}/{DOY:3s}/{YY:2s}p'.format(year=str(amc.dRTK['date']['year']), DOY=amc.dRTK['date']['DoY'], YY=amc.dRTK['date']['YY'])
    dCom['rfile'] = 'BRDC00IGS_R_{year:4s}{DOY:s}0000_01D_MN.rnx.gz'.format(year=str(amc.dRTK['date']['year']), DOY=amc.dRTK['date']['DoY'])

    dRemote['gal'] = dGal
    dRemote['gps'] = dGPS
    dRemote['com'] = dCom

    return dRemote


def doNcFTPDownload(logger: logging.Logger):
    """
    doNcFTPDownload downloads remote files using 'ncftget' program
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # locate 'ncftpget' program
    exeNCFTPGET = location.locateProg('ncftpget', logger)

    # create and change to download directory
    amc.dRTK['local']['YYDOY'] = '{YY:s}{DOY:s}'.format(YY=amc.dRTK['date']['YY'], DOY=amc.dRTK['date']['DoY'])
    amc.dRTK['local']['dir'] = os.path.join(amc.dRTK['local']['root'], amc.dRTK['local']['YYDOY'])
    amutils.mkdir_p(amc.dRTK['local']['dir'])
    amutils.changeDir(amc.dRTK['local']['dir'])
    logger.info('{func:s}: changed to local directory {dir:s}'.format(dir=amc.dRTK['local']['dir'], func=cFuncName))

    for gnss in amc.dRTK['remote'].keys():
        logger.info('{func:s}: downloading for {gnss:s} RINEX Nav {nav:s}'.format(gnss=gnss, nav=amc.dRTK['remote'][gnss]['rfile'], func=cFuncName))

        cmdNCFTPGET = '{prog:s} -u {user:s} -p {passwd:s} -v  ftp://{host:s}/{rpath}/{rfile:s}'.format(prog=exeNCFTPGET, user=amc.dRTK['ftp']['user'], passwd=amc.dRTK['ftp']['passwd'], host=amc.dRTK['ftp']['server'], rpath=amc.dRTK['remote'][gnss]['rpath'], rfile=amc.dRTK['remote'][gnss]['rfile'])

        logger.info('{func:s}: ... running {cmd:s}'.format(cmd=cmdNCFTPGET, func=cFuncName))

        # run the program
        exeprogram.subProcessDisplayStdErr(cmd=cmdNCFTPGET, verbose=True)


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
    amc.dRTK['local']['root'], amc.dRTK['ftp']['server'], dDate['year'], dDate['daynr'], overwrite, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=amc.dRTK['local']['root'], logLevels=logLevels)

    # get the YY and DOY values as string
    dDate['YY'] = dDate['year'][2:]
    dDate['DoY'] = '{:03d}'.format(dDate['daynr'])

    # create the remote/local directories and filenames to download the individual/combined RINEX Navigation files from
    amc.dRTK['remote'] = createRemoteFTPInfo(logger=logger)

    # download the RINEX navigation files using ncftpget
    doNcFTPDownload(logger=logger)

    # report to the user
    logger.info('{func:s}: amc.dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4)))

    # copy temp log file to the YYDOY directory
    copyfile(log_name, os.path.join(amc.dRTK['local']['dir'], 'pyftposnav.log'))
    os.remove(log_name)


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)

    # ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2019/134/19l/BRUX00BEL_R_20191340000_01D_EN.rnx.gz
    # ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2019/134/19n/brdc1340.19n.Z
    # ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2019/134/19p/BRDC00IGS_R_20191340000_01D_MN.rnx.gz
