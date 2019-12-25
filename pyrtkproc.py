#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
from json import encoder
import pandas as pd
import logging

import am_config as amc
from ampyutils import location, exeprogram, amutils
from rnx2rtkp import template_rnx2rtkp
from rnx2rtkp import rtklibconstants as rtkc

__author__ = 'amuls'


def treatCmdOpts(argv):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string

    url = "ftp://cddis.gsfc.nasa.gov/pub/gps/data/daily/2018/318/18d/CORD00ARG_R_20183180000_01D_30S_MO.crx.gz"

    """
    helpTxt = os.path.basename(__file__) + ' processes GNSS Observations with RTKLib'

    # create lists from dict values used as choices for arguments
    lstPosMode = list(rtkc.dPosMode.values())
    lstNavSys = list(rtkc.dNavSys.values())
    lstIono = list(rtkc.dIono.values())
    lstTropo = list(rtkc.dTropo.values())
    lstSatEph = list(rtkc.dSatEph.values())
    # lstFreq = list(rtkc.dFreq.keys())

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)

    parser.add_argument('-d', '--dir', help='project root directory (default {:s})'.format(colored('./', 'green')), required=False, default='./', type=str)
    parser.add_argument('-r', '--roverobs', help='rover observation file', required=True, type=str)
    parser.add_argument('-m', '--mode', help='rnx2rtkp positioning mode (default {:s})'.format(colored(lstPosMode[0], 'green')), required=False, default=lstPosMode[0], type=str, choices=lstPosMode)
    parser.add_argument('-f', '--freq', help='Select frequencies for relative mode (default {:s}, choices are 1:l1, 2:l1+l2, 3:l1+l2+l5, 4:l1+l2+l5+l6, 5:l1+l2+l5+l6+l7)'.format(colored(1, 'green')), required=False, default=1, choices=range(1, 6), type=int)
    parser.add_argument('-c', '--cutoff', help='cutoff angle [degrees] (default {:s})'.format(colored('5', 'green')), choices=range(0, 15), required=False, default=5, type=int)
    parser.add_argument('-b', '--baseobs', help='base station observation file', required=False, default='', type=str)

    parser.add_argument('-e', '--ephem', help='(list of) ephemeris files', nargs='+', required=True, type=str)

    parser.add_argument('-g', '--gnss', help='GNSS systems to process (default={:s})'.format(colored(lstNavSys[3], 'green')), required=False, default=lstNavSys[3], choices=lstNavSys)

    parser.add_argument('-s', '--sateph', help='type of ephemerides used (default {:s})'.format(colored(lstSatEph[0], 'green')), default=lstSatEph[0], required=False, choices=lstSatEph, type=str)
    parser.add_argument('-a', '--atmtropo', help='select troposheric correction (default {:s})'.format(colored(lstTropo[1], 'green')), default=lstTropo[1], required=False, type=str)
    parser.add_argument('-i', '--iono', help='select ionospheric correction (default {:s})'.format(colored(lstIono[1], 'green')), required=False, default=lstIono[1], choices=lstIono, type=str)

    parser.add_argument('-t', '--template', help='rnx2rtkp template file (default {:s})'.format(colored('rnx2rtkp.tmpl', 'green')), required=False, type=str, default='~/amPython/pyRTKLib/rnx2rtkp.tmpl')

    parser.add_argument('-o', '--overwrite', help='overwrite intermediate files (default False)', action='store_true', required=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    args = parser.parse_args(argv[1:])

    # return arguments
    return args.dir, args.roverobs, args.mode, args.freq, args.cutoff, args.baseobs, args.ephem, args.gnss, args.sateph, args.atmtropo, args.iono, args.template, args.overwrite, args.logging


def checkValidityArgs(logger: logging.Logger) -> bool:
    """
    checks for existence of dirs/files and also for presence of base station observation when posmode > 0 (single)
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # change to baseDir, everything is relative to this directory
    amc.dRTK['rootDir'] = os.path.expanduser(amc.dRTK['rootDir'])
    if not amutils.changeDir(amc.dRTK['rootDir']):
        logger.error('{func:s}: could not change to {basedir:s}.\n'.format(func=cFuncName, basedir=amc.dRTK['rootDir']))
        return amc.E_INVALID_ARGS

    logger.info('{func:s}: changed to directory {basedir:s}'.format(func=cFuncName, basedir=colored(amc.dRTK['rootDir'], 'green')))

    # create the rtkp directory for storing the result files according to the GNSS system processed
    amc.dRTK['rtkDir'] = os.path.join(amc.dRTK['rootDir'], 'rtkp', amc.dRTK['GNSS'])
    amutils.mkdir_p(amc.dRTK['rtkDir'])

    # check existence of rover observation file
    if not os.access(amc.dRTK['roverObs'], os.R_OK):
        logger.error('{func:s}: rover observation file {rover:s} not accessible.\n'.format(func=cFuncName, rover=amc.dRTK['roverObs']))
        return amc.E_FILE_NOT_EXIST
    else:
        # name the result/statistics file calculated by rnx2rtkp
        amc.dRTK['filePos'] = '{rover:s}.pos'.format(rover=os.path.join('rtkp', amc.dRTK['GNSS'], amc.dRTK['roverObs'].replace('.', '-')))
        amc.dRTK['fileStat'] = '{rover:s}.pos.stat'.format(rover=os.path.join('rtkp', amc.dRTK['GNSS'], amc.dRTK['roverObs'].replace('.', '-')))

    # check existence of ephemeris file
    for _, ephemFile in enumerate(amc.dRTK['ephems']):
        if not os.access(ephemFile, os.R_OK):
            logger.error('{func:s}: ephemeris file {ephem:s} not accessible.\n'.format(func=cFuncName, ephem=ephemFile))
            return amc.E_FILE_NOT_EXIST

    # check existence of template file
    amc.dRTK['template'] = os.path.join(amc.dRTK['rootDir'], os.path.expanduser(amc.dRTK['template']))
    if not os.access(os.path.abspath(amc.dRTK['template']), os.R_OK):
        logger.error('{func:s}: rnx2rtkp (rtkpos) template file {tmpl:s} not accessible.\n'.format(func=cFuncName, tmpl=amc.dRTK['template']))
        return amc.E_FILE_NOT_EXIST

    # check if base station observation file is present when the positioning mode is not single (=0)
    if amc.dRTK['posMode'] != 'single':
        if not os.access(amc.dRTK['baseObs'], os.R_OK):
            logger.error('{func:s}: reference station observation file {base:s} not accessible.\n'.format(func=cFuncName, base=amc.dRTK['baseObs']))
            return amc.E_FILE_NOT_EXIST

    return amc.E_SUCCESS


def main(argv):
    """
    pyRnxProc processes RINEX data using 'amrnx2rtkp'

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # pandas options
    pd.options.display.max_rows = 40
    pd.options.display.max_columns = 36
    pd.options.display.width = 2000

    # limit float precision
    encoder.FLOAT_REPR = lambda o: format(o, '.3f')

    # treat command line options
    rootDir, roverObs, posMode, freq, cutOff, baseObs, ephemeris, gnss, typeEphem, tropo, iono, template, overwrite, logLevels = treatCmdOpts(argv)

    # create logging for better debugging
    logger = amc.createLoggers(baseName=os.path.basename(__file__), dir=rootDir, logLevels=logLevels)

    # store cli parameters
    amc.dRTK = {}
    amc.dRTK['rootDir'] = rootDir
    amc.dRTK['roverObs'] = roverObs
    amc.dRTK['posMode'] = posMode
    amc.dRTK['freq'] = [v for k, v in rtkc.dFreq.items() if k == freq][0]
    amc.dRTK['cutOff'] = cutOff
    amc.dRTK['baseObs'] = baseObs
    amc.dRTK['ephems'] = ephemeris
    amc.dRTK['GNSS'] = gnss
    amc.dRTK['typeEphem'] = typeEphem
    amc.dRTK['Tropo'] = tropo
    amc.dRTK['Iono'] = iono
    amc.dRTK['template'] = template

    # check validity of passed arguments
    retCode = checkValidityArgs(logger=logger)
    if retCode != amc.E_SUCCESS:
        logger.error('{func:s}: Program exits with code {error:s}'.format(func=cFuncName, error=colored('{!s}'.format(retCode), 'red')))
        sys.exit(retCode)

    # create the configuration file for the GNSSs to process
    amc.dRTK['config'] = os.path.join(amc.dRTK['rtkDir'], '{rover:s}-{syst:s}.conf'.format(rover=amc.dRTK['roverObs'].split('.')[0], syst=amc.dRTK['GNSS'].upper()))

    logger.info('{func:s}: Creating {syst:s} configuration file {conf:s}'.format(func=cFuncName, syst=colored(gnss, 'green'), conf=colored(amc.dRTK['config'], 'green')))

    # create the settings used for replacing the fields in the template file
    template_rnx2rtkp.create_rnx2rtkp_settings(overwrite=overwrite, logger=logger)

    template_rnx2rtkp.create_rnx2rtkp_template(cfgFile=amc.dRTK['config'], overwrite=overwrite, logger=logger)

    logger.info('{func:s}: amc.dRTK = \n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4)))

    # locate the rnx2rtkp program used for execution
    exeRNX2RTKP = location.locateProg('rnx2rtkp', logger)

    cmdRNX2RTKP = '{prog:s} -k {conf:s} -o {pos:s} {rover:s} {base:s} {nav:s}'.format(prog=exeRNX2RTKP, conf=amc.dRTK['config'], pos=amc.dRTK['filePos'], rover=amc.dRTK['roverObs'], base=amc.dRTK['baseObs'], nav=' '.join(amc.dRTK['ephems']))

    logger.info('{func:s}: Running:\n{cmd:s}'.format(func=cFuncName, cmd=colored(cmdRNX2RTKP, 'green')))

    # run the program
    if amc.dLogLevel[logLevels[0]] >= amc.dLogLevel['INFO']:
        exeprogram.subProcessDisplayStdErr(cmd=cmdRNX2RTKP, verbose=True)
    else:
        exeprogram.subProcessDisplayStdErr(cmd=cmdRNX2RTKP, verbose=False)

    # inform user
    logger.info('{func:s}: Created position file: {pos:s}'.format(func=cFuncName, pos=colored(amc.dRTK['filePos'], 'blue')))
    logger.info('{func:s}: Created statistics file: {stat:s}'.format(func=cFuncName, stat=colored(amc.dRTK['fileStat'], 'blue')))


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
