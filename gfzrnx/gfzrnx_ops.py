import os
import sys
from termcolor import colored
import json
import logging
from datetime import datetime
import tempfile

import am_config as amc
from ampyutils import amutils

__author__ = 'amuls'


def rnxobs_header_info(dTmpRnx: dict, logger: logging.Logger):
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
    dSatSysts['select'] = list(dObsHdr['file']['satsys'])
    if ('E' in dSatSysts['select']) and ('G' in dSatSysts['select']):
        dSatSysts['select'] += 'M'  # GPS/Galileo combined

    for _, satsys in enumerate(dObsHdr['file']['satsys']):
        dSatSyst = {}

        dSatSyst['name'] = amc.dGNSSs.get(satsys)
        dSatSyst['satsys'] = satsys
        dSatSyst['sysfrq'] = dObsHdr['file']['sysfrq'][satsys]
        dSatSyst['systyp'] = dObsHdr['file']['systyp'][satsys]
        dSatSyst['sysobs'] = dObsHdr['file']['sysobs'][satsys]
        # create the station name for this GNSS from amc.dGNSSs and replace the current station name by 'marker'
        if (satsys == 'E') and (dSatSyst['sysfrq'] == ['1', '6']):
            marker = 'GPRS'
        else:
            marker = ''.join(amc.dGNSSs[satsys].split())[:4].upper()
        dSatSyst['marker'] = marker

        dSatSysts[satsys] = dSatSyst

    # check whether we have both GPS & GALILEO, if so make also the combined RINEX Obs/Nav files
    if ('M' in dSatSysts['select']):
        dSatSyst = {}

        satsys = 'M'
        dSatSyst['name'] = amc.dGNSSs.get(satsys)
        dSatSyst['satsys'] = 'EG'
        dSatSyst['sysfrq'] = list(sorted(set(dObsHdr['file']['sysfrq']['E'] + dObsHdr['file']['sysfrq']['G'])))
        dSatSyst['systyp'] = list(sorted(set(dObsHdr['file']['systyp']['E'] + dObsHdr['file']['systyp']['G'])))
        dSatSyst['sysobs'] = list(sorted(set(dObsHdr['file']['sysobs']['E'] + dObsHdr['file']['sysobs']['G'])))
        dSatSyst['marker'] = ''.join(amc.dGNSSs[satsys].split())[:4].upper()

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
        logger.info('{func:s}:    satellite system: {satsys:s} ({gnss:s})'.format(satsys=satsys, gnss=amc.dGNSSs.get(satsys), func=cFuncName))
        logger.info('{func:s}:        frequencies: {freqs!s}'.format(freqs=dObsHdr['file']['sysfrq'][satsys], func=cFuncName))
        logger.info('{func:s}:       system types: {systypes!s}'.format(systypes=dObsHdr['file']['systyp'][satsys], func=cFuncName))
        logger.info('{func:s}:        observables: {obs!s}'.format(obs=dObsHdr['file']['sysobs'][satsys], func=cFuncName))

    # logger.info('{func:s}: dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    pass


def rnxobs_statistics_file(dTmpRnx: dict, logger: logging.Logger):
    """
    rnxobs_statistics_file creates the observation statistics per satellite system
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the satsys option for extracting the observation statistics for only Galileo & GPS (if both present)
    satsystems = ''.join(amc.dRTK['rnx']['gnss']['select']).replace('M', '')

    # create the CLI command for getting observation statistics in a temporary file
    dTmpRnx['obsstat'] = dTmpRnx['obs'] + '.obsstat'
    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', dTmpRnx['obs'], '-stk_obs', '-satsys', satsystems, '-fout', dTmpRnx['obsstat'], '-f']
    logger.info('{func:s}: extracting RINEX observation statistics'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    # open the obsstat file for reading line by line
    finp = open(dTmpRnx['obsstat'], 'r')

    # read in the obsstat file per satellite system
    for _, satsys in enumerate(satsystems):
        # reset to start of file
        finp.seek(0, os.SEEK_SET)
        # create the directory under gfzrnx for this marker
        marker_dir = os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][satsys]['marker'])
        amutils.mkdir_p(marker_dir)

        amc.dRTK['rnx']['gnss'][satsys]['obsstat'] = '{marker:s}{doy:03d}0-{yy:02d}O.obsstat'.format(marker=amc.dRTK['rnx']['gnss'][satsys]['marker'], doy=amc.dRTK['rnx']['times']['doy'], yy=amc.dRTK['rnx']['times']['yy'])

        # create the file with the observation statistics for satsys
        logger.info('{func:s}: creating observation statistics {stat:s}'.format(stat=colored(amc.dRTK['rnx']['gnss'][satsys]['obsstat'], 'green'), func=cFuncName))
        with open(os.path.join(marker_dir, amc.dRTK['rnx']['gnss'][satsys]['obsstat']), "w") as fout:
            for line in finp.readlines():
                try:
                    if satsys == line[10]:
                        # found a line belonging to this satsys, replace the original marker name
                        fout.write('{line:s}'.format(line=line[1:].replace(amc.dRTK['rnx']['marker'], amc.dRTK['rnx']['gnss'][satsys]['marker'])))
                except IndexError:
                    # skip empty lines
                    pass

    # close the obsstat file
    finp.close()

    pass


def gnss_rinex_creation(dTmpRnx: dict, logger: logging.Logger):
    """
    gnss_rinex_creation creates the RINEX observation/navigation files per satsys
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    for rnx_type in ('obs', 'nav'):
        # create the corresponding RINEX Obs/Nav file for each individual satellite system
        for _, satsys in enumerate(amc.dRTK['rnx']['gnss']['select']):
            # determin ethe name of the RINEX file to be created
            amc.dRTK['rnx']['gnss'][satsys][rnx_type] = '{marker:s}{doy:03d}0.{yy:02d}{ext:s}'.format(marker=amc.dRTK['rnx']['gnss'][satsys]['marker'], doy=amc.dRTK['rnx']['times']['doy'], yy=amc.dRTK['rnx']['times']['yy'], ext=amc.dRnx_ext[satsys][rnx_type])

            if rnx_type == 'obs':
                out_dir = tempfile.gettempdir()
                dTmpRnx[amc.dRTK['rnx']['gnss'][satsys]['marker']] = os.path.join(out_dir, amc.dRTK['rnx']['gnss'][satsys][rnx_type])
            else:
                out_dir = amc.dRTK['rinexDir']

            # create the RINEX OBS or NAV file for this satsys in final dir for NAV and temporay dir for OBS
            args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', dTmpRnx[rnx_type], '-fout', os.path.join(out_dir, amc.dRTK['rnx']['gnss'][satsys][rnx_type]), '-satsys', amc.dRTK['rnx']['gnss'][satsys]['satsys'], '-f', '-chk', '-kv']
            logger.info('{func:s}: creating RINEX file {name:s}'.format(name=colored(amc.dRTK['rnx']['gnss'][satsys][rnx_type], 'green'), func=cFuncName))

            # perform the RINEX creation
            amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

            # when RINEX OBS adjust the headers by editing via CRUX file
            if rnx_type == 'obs':
                # create a CRUX file to correct the header info for this satsys
                crux_file = create_crux(satsys=satsys, logger=logger)

                args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', os.path.join(out_dir, amc.dRTK['rnx']['gnss'][satsys][rnx_type]), '-f', '-fout', os.path.join(amc.dRTK['rinexDir'], amc.dRTK['rnx']['gnss'][satsys][rnx_type]), '-crux', crux_file]

                # perform the RINEX creation
                amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

                # remove temporary file created
                os.remove(crux_file)

                if satsys != 'M':
                    # create e ASCII display of visibility of the SVs in the observation file
                    # amc.dRTK['rnx']['gnss'][satsys]['prns'] = amc.dRTK['rnx']['gnss'][satsys][rnx_type].replace('.', '-') + '.prns'

                    # args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-f', '-stk_epo', amc.dRTK['interval'], '-finp', os.path.join(amc.dRTK['rinexDir'], amc.dRTK['rnx']['gnss'][satsys][rnx_type]), '-fout', os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][satsys]['marker'], amc.dRTK['rnx']['gnss'][satsys]['prns'])]

                    # logger.info('{func:s}: Creating ASCII SVs display {prns:s}'.format(prns=colored(amc.dRTK['rnx']['gnss'][satsys]['prns'], 'green'), func=cFuncName))

                    # # run the program
                    # # gfzrnx -stk_epo 300-finp data/P1710171.20O
                    # amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

                    # # display the ASCII SVs overview
                    # with open(os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][satsys]['marker'], amc.dRTK['rnx']['gnss'][satsys]['prns'])) as f:
                    #     for line in f:
                    #         if line.startswith(' ST'):
                    #             logger.info(line[:-1])

                    # create e ASCII display of visibility of the SVs in the observation file
                    amc.dRTK['rnx']['gnss'][satsys]['prns'] = create_svs_ascii_plot(satsys=satsys, rnx_type=rnx_type, logger=logger)

                    # create the tabular observation file
                    amc.dRTK['rnx']['gnss'][satsys]['obstab'] = create_tabular_observation(satsys=satsys, rnx_type=rnx_type, logger=logger)

    pass


def create_crux(satsys: str, logger: logging.Logger) -> str:
    """
    create_crux creates a crux file to use for editing the RINEX observation header
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    crux_name = os.path.join(tempfile.gettempdir(), tempfile.NamedTemporaryFile(prefix="gfzrnx_", suffix=".crux").name)

    logger.info('{func:s}: creating crux-file {crux:s}'.format(crux=colored(crux_name, 'green'), func=cFuncName))
    with open(crux_name, 'w') as fcrux:
        fcrux.write('update_insert:\n\n')
        fcrux.write('O - ALL:\n\n')  # update is for Observation file

        fcrux.write('"APPROX POSITION XYZ" : {')
        for i, crd in enumerate(amc.dRTK['ant_crds']):
            fcrux.write(' {nr:d}:"{crd:.4f}"'.format(nr=i, crd=crd))
            if i < 2:
                fcrux.write(',')
        fcrux.write('}\n')

        fcrux.write('"MARKER NAME" : { ')
        fcrux.write('0:"{marker:s}"'.format(marker=amc.dRTK['rnx']['gnss'][satsys]['marker']))
        fcrux.write('}\n')

        fcrux.write('"MARKER NUMBER" : { 0:"ERM01"}\n')
        fcrux.write('"OBSERVER / AGENCY" : { 0:"amuls", 1:"RMA"}\n')

    fcrux.close()

    return crux_name


def create_tabular_observation(satsys: str, rnx_type:str, logger: logging.Logger) -> str:
    """
    create_tabular_observation creates a tabular view of all observables for all SVs in RINEX obs file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create a tabular output file containing the observables for this satsys
    obs_tabular = amc.dRTK['rnx']['gnss'][satsys][rnx_type].replace('.', '-') + '.obstab'

    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-f', '-finp', os.path.join(amc.dRTK['rinexDir'], amc.dRTK['rnx']['gnss'][satsys][rnx_type]), '-fout', os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][satsys]['marker'], obs_tabular), '-tab_obs', '-satsys', satsys]

    logger.info('{func:s}: Creating observation tabular output {obstab:s}'.format(obstab=colored(obs_tabular, 'green'), func=cFuncName))

    # run the program
    # gfzrnx -finp GALI1340.19O -tab_obs -satsys E  2> /dev/null -fout /tmp/E-ALL.t
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    # return the created file name
    return obs_tabular


def create_svs_ascii_plot(satsys: str, rnx_type:str, logger: logging.Logger) -> str:
    """
    create_svs_ascii_plot creates a ASCII plot of SVs visibility according to RINEX observation file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    prns_visibility = amc.dRTK['rnx']['gnss'][satsys][rnx_type].replace('.', '-') + '.prns'

    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-f', '-stk_epo', amc.dRTK['interval'], '-finp', os.path.join(amc.dRTK['rinexDir'], amc.dRTK['rnx']['gnss'][satsys][rnx_type]), '-fout', os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][satsys]['marker'], prns_visibility)]

    logger.info('{func:s}: Creating ASCII SVs display {prns:s}'.format(prns=colored(prns_visibility, 'green'), func=cFuncName))

    # run the program
    # gfzrnx -stk_epo 300-finp data/P1710171.20O
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    # display the ASCII SVs overview
    with open(os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][satsys]['marker'], prns_visibility)) as f:
        for line in f:
            if line.startswith(' ST'):
                logger.info(line[:-1])

    return prns_visibility
