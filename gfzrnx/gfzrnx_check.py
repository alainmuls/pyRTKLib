import os
import sys
from termcolor import colored
import json
import logging

import am_config as amc
from ampyutils import amutils

__author__ = 'amuls'


def rnxobs_header_info(dTmpRnx: dict, dGNSSs: dict, logger: logging.Logger):
    """
    rnxobs_header_info extracts the basic hedaer info from the rinex file
    and stores it in a JSON structure
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the CLI command for extracting header information into a JSON structure
    amc.dRTK['rnx'] = {}
    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', dTmpRnx['obs'], '-meta', 'basic:json', '-fout', dTmpRnx['obs'] + '.json', '-f']
    logger.info('{func:s}: extracting RINEX observation header'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    with open(dTmpRnx['obs'] + '.json', 'r') as f:
        amc.dRTK['rnx']['obshdr'] = json.load(f)

    # report information to user
    logger.info('{func:s}: RINEX observation basic information'.format(func=cFuncName))

    logger.info('{func:s}:    times:'.format(func=cFuncName))
    logger.info('{func:s}:          first: {first!s}'.format(first=amc.dRTK['rnx']['obshdr']['data']['epoch']['first'], func=cFuncName))
    logger.info('{func:s}:           last: {last!s}'.format(last=amc.dRTK['rnx']['obshdr']['data']['epoch']['last'], func=cFuncName))
    logger.info('{func:s}:       interval: {last!s}'.format(last=amc.dRTK['rnx']['obshdr']['file']['interval'], func=cFuncName))

    for _, satsys in enumerate(amc.dRTK['rnx']['obshdr']['file']['satsys']):
        logger.info('{func:s}:    satellite system: {satsys:s} ({gnss:s})'.format(satsys=satsys, gnss=dGNSSs.get(satsys), func=cFuncName))
        logger.info('{func:s}:        frequencies: {freqs!s}'.format(freqs=amc.dRTK['rnx']['obshdr']['file']['sysfrq'][satsys], func=cFuncName))
        logger.info('{func:s}:       system types: {systypes!s}'.format(systypes=amc.dRTK['rnx']['obshdr']['file']['systyp'][satsys], func=cFuncName))
        logger.info('{func:s}:        observables: {obs!s}'.format(obs=amc.dRTK['rnx']['obshdr']['file']['sysobs'][satsys], func=cFuncName))

    # logger.info('{func:s}: amc.dRTK[rnxchk][obshdr] =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK['rnx']['obshdr'], sort_keys=False, indent=4)))

    # determine the DOY, YY for later usage

    pass


def rnxobs_statistics(dTmpRnx: dict, dGNSSs: dict, logger: logging.Logger):
    """
    rnxobs_statistics gets the statistics of the observations in the RINEX observation file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the CLI command for getting observation statistics in a temporary file
    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', dTmpRnx['obs'], '-stk_obs', '-satsys', amc.dRTK['rnx']['obshdr']['file']['satsys'], '-fout', dTmpRnx['obs'] + '.obsstat', '-f']
    logger.info('{func:s}: extracting RINEX observation statistics'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)


    # gfzrnx -finp /tmp/BEGP0110.19O -fout /tmp/BEGPCOM.t -stk_obs -satsys GE -f 2> /dev/null
