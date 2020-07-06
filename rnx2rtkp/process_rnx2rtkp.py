import sys
import os
from termcolor import colored
import logging

import am_config as amc
from ampyutils import location, exeprogram, amutils


def process_rover(dRover, dProj, logger: logging.Logger, overwrite=False):
    """
    process_rover processes the rover according to the settings file

    :params dRover: information of the rover station
    :type dRover: dictionary
    :params dProj: information about project
    :type dProj: dictionary
    """
    cFuncName = amc.cBaseName + ': ' + colored(sys._getframe().f_code.co_name, 'green')

    # create RNX2RTKP command line options
    amc.dSettings['PROGS']['rnx2rtkp'] = location.locateProg('rnx2rtkp')

    # convert directory for the specified positioning mode and rover
    dRover['rtkp_dir'] = os.path.join(amc.dSettings['PROJECT']['out_dir'], dProj['posmode'], dRover['name'])
    amutils.mkdir_p(dRover['rtkp_dir'])
    dRover['rtkp_pos'] = os.path.join(dRover['rtkp_dir'], '{stat:s}-{yy:d}{doy:d}.pos'.format(stat=dRover['name'], yy=amc.dSettings['PROJECT']['iYY'], doy=amc.dSettings['PROJECT']['iDOY']))

    # dRover['posfile'] = dRover
    script = '{cmd:s} -k {conf:s} '.format(cmd=amc.dSettings['PROGS']['rnx2rtkp'], conf=amc.dSettings['RNX2RTKP']['rtkpconf'])

    if dProj['posmode'].lower() == 'single':
        logger.info('{func:s}\n... {mode:s}  processing station {stat:s}'.format(func=cFuncName, mode=colored(amc.dSettings['PROJECT']['posmode'], 'yellow'), stat=colored(dRover['name'], 'yellow')))

        script += '-o {out:s} {obs:s} {nav:s}'.format(out=dRover['rtkp_pos'], obs=dRover['rinex_name'], nav=amc.dSettings['NAV']['com'])
    else:
        logger.info('{func:s}\n... {mode:s} processing station {rvr:s}, reference {base:s}'.format(func=cFuncName, mode=colored(amc.dSettings['PROJECT']['posmode'], 'yellow'), rvr=colored(dRover['name'], 'yellow'), base=colored(amc.dSettings['BASE']['site'], 'yellow')))

        if dProj['posmode'].lower() in ['dgps', 'static']:
            script += '-o {out:s} -r {xyz:s} {obs:s} {ref:s} {nav:s}'.format(out=dRover['rtkp_pos'], obs=dRover['rinex_name'], ref=amc.dSettings['BASE']['rinex'], nav=amc.dSettings['NAV']['com_rnx3'], xyz=amc.dSettings['BASE']['cart'])
        else:
            sys.stderr.write('{func:s}\n   ... wrong positioning mode for RNX2RTKP: {mode:s}'.format(func=cFuncName, mode=dProj['posmode']))

    logger.info('{func:s}: executing = {script!s}'.format(script=script, func=cfunc))
    sys.exit(6)

    # execute script
    exeprogram.subProcessLogStdErr(command=script, logger=logger)
    pass
