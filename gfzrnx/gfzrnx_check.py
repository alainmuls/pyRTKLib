import os
import sys
from termcolor import colored
import json
import logging
from datetime import datetime

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
    dTmpRnx['json'] = dTmpRnx['obs'] + '.json'
    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', dTmpRnx['obs'], '-meta', 'basic:json', '-fout', dTmpRnx['json'], '-f']
    logger.info('{func:s}: extracting RINEX observation header'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    with open(dTmpRnx['json'], 'r') as f:
        dObsHdr = json.load(f)

    # collect time info
    dTimes = {}
    dTimes['DT'] = datetime.strptime(dObsHdr['data']['epoch']['first'][:-1], '%Y %m %d %H %M %S.%f')
    dTimes['date'] = dTimes['DT'].date()
    dTimes['doy'] = dTimes['DT'].timetuple().tm_yday
    dTimes['year'] = dTimes['DT'].timetuple().tm_year
    dTimes['yy'] = dTimes['year'] % 100

    # collect info per satellite system
    dSatSysts = {}
    dSatSysts['comb'] = dObsHdr['file']['satsys']
    for _, satsys in enumerate(dObsHdr['file']['satsys']):
        dSatSyst = {}

        dSatSyst['satsys'] = satsys
        dSatSyst['name'] = dGNSSs.get(satsys)
        dSatSyst['sysfrq'] = dObsHdr['file']['sysfrq'][satsys]
        dSatSyst['systyp'] = dObsHdr['file']['systyp'][satsys]
        dSatSyst['sysobs'] = dObsHdr['file']['sysobs'][satsys]

        dSatSysts[satsys] = dSatSyst

    # store the usefull info
    amc.dRTK['rnx'] = {}
    amc.dRTK['rnx']['times'] = dTimes
    amc.dRTK['rnx']['gnss'] = dSatSysts
    amc.dRTK['rnx']['marker'] = dObsHdr['site']['name']

    # report information to user
    logger.info('{func:s}: RINEX observation basic information'.format(func=cFuncName))

    logger.info('{func:s}:    marker: {marker:s}'.format(marker=dObsHdr['site']['name'], func=cFuncName))
    logger.info('{func:s}:    times:'.format(func=cFuncName))
    logger.info('{func:s}:          first: {first!s}'.format(first=dObsHdr['data']['epoch']['first'], func=cFuncName))
    logger.info('{func:s}:           last: {last!s}'.format(last=dObsHdr['data']['epoch']['last'], func=cFuncName))
    logger.info('{func:s}:       interval: {interval:.2f}'.format(interval=float(dObsHdr['file']['interval']), func=cFuncName))
    logger.info('{func:s}:         DOY/YY: {DOY:03d}/{YY:02d}'.format(DOY=dTimes['doy'], YY=dTimes['yy'], func=cFuncName))

    for _, satsys in enumerate(dObsHdr['file']['satsys']):
        logger.info('{func:s}:    satellite system: {satsys:s} ({gnss:s})'.format(satsys=satsys, gnss=dGNSSs.get(satsys), func=cFuncName))
        logger.info('{func:s}:        frequencies: {freqs!s}'.format(freqs=dObsHdr['file']['sysfrq'][satsys], func=cFuncName))
        logger.info('{func:s}:       system types: {systypes!s}'.format(systypes=dObsHdr['file']['systyp'][satsys], func=cFuncName))
        logger.info('{func:s}:        observables: {obs!s}'.format(obs=dObsHdr['file']['sysobs'][satsys], func=cFuncName))

    logger.info('{func:s}: dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    pass


def rnxobs_statistics(dTmpRnx: dict, dGNSSs: dict, logger: logging.Logger):
    """
    rnxobs_statistics gets the statistics of the observations in the RINEX observation file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the CLI command for getting observation statistics in a temporary file
    dTmpRnx['obsstat'] = dTmpRnx['obs'] + '.obsstat'
    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', dTmpRnx['obs'], '-stk_obs', '-satsys', amc.dRTK['rnx']['gnss']['comb'], '-fout', dTmpRnx['obsstat'], '-f']
    logger.info('{func:s}: extracting RINEX observation statistics'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    # open the obsstat file for reading line by line
    finp = open(dTmpRnx['obsstat'], 'r')

    # read in the obsstat file per satellite system
    for _, satsys in enumerate(amc.dRTK['rnx']['gnss']['comb']):
        # reset to start of file
        finp.seek(0, os.SEEK_SET)
        print('-' * 25, end='')
        print(satsys)

        # create the station name for this GNSS from dGNSSs and replace the current station name by 'marker'
        marker = ''.join(dGNSSs[satsys].split())[:4].upper()
        amc.dRTK['rnx']['gnss'][satsys]['marker'] = marker
        print(marker)
        print(amc.dRTK['rnx']['marker'])

        logger.info('{func:s}: dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))

        # create the directory under gfzrnx for this marker
        marker_dir = os.path.join(amc.dRTK['gfzrnxDir'], marker)
        print('marker_dir = {!s}'.format(marker_dir))
        amutils.mkdir_p(marker_dir)

        satsys_obsstat = '{marker:s}{doy:03d}0-{yy:02d}O.obsstat'.format(marker=marker, doy=amc.dRTK['rnx']['times']['doy'], yy=amc.dRTK['rnx']['times']['yy'])
        print(satsys_obsstat)

        for line in finp.readlines():
            try:
                if satsys == line[10]:
                    # found a line belonging to this satellite system, replace the original marker name
                    print('{satsys:s}: {line:s}'.format(satsys=satsys, line=line[1:].replace(amc.dRTK['rnx']['marker'], marker)), end='')
            except IndexError:
                # skip empty lines
                pass

    # close the obsstat file
    finp.close()
    sys.exit(55)

    pass
