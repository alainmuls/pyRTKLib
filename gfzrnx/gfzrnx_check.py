import os
import sys
from termcolor import colored
import json
import logging
from datetime import datetime

import am_config as amc
from ampyutils import amutils

__author__ = 'amuls'


def rnxobs_header_info(dTmpRnx: dict, dGNSSs: dict, logger: logging.Logger) -> dict:
    """
    rnxobs_header_info extracts the basic hedaer info from the rinex file
    and stores it in a JSON structure
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the CLI command for extracting header information into a JSON structure
    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', dTmpRnx['obs'], '-meta', 'basic:json', '-fout', dTmpRnx['obs'] + '.json', '-f']
    logger.info('{func:s}: extracting RINEX observation header'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    with open(dTmpRnx['obs'] + '.json', 'r') as f:
        dObsHdr = json.load(f)

    # store the usefull info
    amc.dRTK['rnx'] = {}
    dTimes = {}
    # date_time_str = '2018-06-29 08:15:27.243860'
    # print(date_time_str)
    # date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')

    # print('Date:', date_time_obj.date())
    # print('Time:', date_time_obj.time())
    # print('Date-time:', date_time_obj)

    # date_time_str = '2019-01-11 00:00:00.0000000'
    # print(date_time_str)
    # date_time_obj = datetime.strptime(date_time_str[:-1], '%Y-%m-%d %H:%M:%S.%f')

    # print('Date:', date_time_obj.date())
    # print('Time:', date_time_obj.time())
    # print('Date-time:', date_time_obj)

    print(dObsHdr['data']['epoch']['first'])
    DT = datetime.strptime(dObsHdr['data']['epoch']['first'][:-1], '%Y %m %d %H %M %S.%f')

    print('DT: ', DT)
    print('Date: ', DT.date())
    print('Time: ', DT.time())

    sys.exit(44)


    # report information to user
    logger.info('{func:s}: RINEX observation basic information'.format(func=cFuncName))

    logger.info('{func:s}:    times:'.format(func=cFuncName))
    logger.info('{func:s}:          first: {first!s}'.format(first=dObsHdr['data']['epoch']['first'], func=cFuncName))
    logger.info('{func:s}:           last: {last!s}'.format(last=dObsHdr['data']['epoch']['last'], func=cFuncName))
    logger.info('{func:s}:       interval: {last!s}'.format(last=dObsHdr['file']['interval'], func=cFuncName))

    for _, satsys in enumerate(dObsHdr['file']['satsys']):
        logger.info('{func:s}:    satellite system: {satsys:s} ({gnss:s})'.format(satsys=satsys, gnss=dGNSSs.get(satsys), func=cFuncName))
        logger.info('{func:s}:        frequencies: {freqs!s}'.format(freqs=dObsHdr['file']['sysfrq'][satsys], func=cFuncName))
        logger.info('{func:s}:       system types: {systypes!s}'.format(systypes=dObsHdr['file']['systyp'][satsys], func=cFuncName))
        logger.info('{func:s}:        observables: {obs!s}'.format(obs=dObsHdr['file']['sysobs'][satsys], func=cFuncName))

    # logger.info('{func:s}: amc.dRTK[rnxchk][obshdr] =\n{json!s}'.format(func=cFuncName, json=json.dumps(dObsHdr, sort_keys=False, indent=4)))

    # determine the DOY, YY for later usage

    return dObsHdr


def rnxobs_statistics(dObsHdr: dict, dTmpRnx: dict, dGNSSs: dict, logger: logging.Logger):
    """
    rnxobs_statistics gets the statistics of the observations in the RINEX observation file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the CLI command for getting observation statistics in a temporary file
    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', dTmpRnx['obs'], '-stk_obs', '-satsys', dObsHdr['file']['satsys'], '-fout', dTmpRnx['obs'] + '.obsstat', '-f']
    logger.info('{func:s}: extracting RINEX observation statistics'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)


    # gfzrnx -finp /tmp/BEGP0110.19O -fout /tmp/BEGPCOM.t -stk_obs -satsys GE -f 2> /dev/null
