import sys
import os
from termcolor import colored
import json
from string import Template
import logging

import am_config as amc
from rnx2rtkp import rtklibconstants as rtkc


def create_rnx2rtkp_settings(logger: logging.Logger, overwrite: str = False):
    """
    createRnxéRTKPSettings creates the settings dictionary used for filling in the template for a selected GNSS system
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: creates settings dictionary for filling the rnx2rtkp template'.format(func=cFuncName))

    amc.dSettings = {}

    amc.dSettings['navFiles'] = ' '.join(amc.dRTK['ephems'])
    amc.dSettings['GNSSnum'] = [key for key, value in rtkc.dNavSys.items() if value == amc.dRTK['GNSS']][0]
    amc.dSettings['freq'] = [k for k,v in rtkc.dFreq.items() if v == amc.dRTK['freq']][0]

    for setting in 'GNSS', 'rootDir', 'roverObs', 'cutOff', 'posMode', 'typeEphem', 'baseObs', 'Tropo', 'Iono', 'filePos', 'fileStat', 'rtkDir':
        amc.dSettings[setting] = amc.dRTK[setting]

    # check if we must set the base station
    if amc.dRTK['posMode'] != 'single':
        amc.dSettings['description'] = '{syst:s}: Processing station {rover:s} with reference {base:s}'.format(syst=amc.dRTK['GNSS'].upper(), rover=amc.dSettings['roverObs'], base=amc.dSettings['baseObs'])
    else:
        amc.dSettings['description'] = '{syst:s}: Processing station {rover:s}'.format(syst=amc.dRTK['GNSS'].upper(), rover=amc.dSettings['roverObs'])

    logger.info('{func:s}: created dSettings =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dSettings, sort_keys=False, indent=4)))

    pass


def create_rnx2rtkp_template(cfgFile: str, logger: logging.Logger, overwrite: str = False):
    """
    create_rnx2rtkp_template creates the configuration file for processing  and stores them
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: creates rnx2rtkp configuration file based on settings dictionary dSettings'.format(func=cFuncName))

    logger.info('{func:s}: using rnx2rtkp template file {tmpl!s}'.format(func=cFuncName, tmpl=amc.dRTK['template']))

    try:
        with open(amc.dRTK['template']) as f:
            tmplData = Template(f.read())
            logger.debug('{func:s}: read tmplData = {tmpl!r}'.format(func=cFuncName, tmpl=tmplData))
            curTemplate = tmplData.substitute(amc.dSettings)
            logger.debug('{func:s}: created template\n{tmpl!s}'.format(func=cFuncName, tmpl=curTemplate))
    except KeyError as e:
        logger.error('{func:s}: template fill returned key error = {err!s}'.format(func=cFuncName, err=e))
    except Exception as e2:
        logger.error('{func:s}: could not read template file {tmpl:s}. Error code = {err!s}'.format(func=cFuncName, tmpl=colored(amc.dRTK['template'], 'red'), err=e2))
        sys.exit(amc.E_FILE_NOT_EXIST)

    try:
        # store the filled template
        logger.info('{func:s}: storing rnx2rtkp configuration file in {cfg:s}'.format(func=cFuncName, cfg=cfgFile))

        with open(cfgFile, 'w') as f:
            f.write(curTemplate)
    except Exception:
        logger.error('{func:s}: could not create template file {cfg:s}\n'.format(func=cFuncName, cfg=colored(cfgFile, 'red')))
        sys.exit(amc.E_FILE_NOT_EXIST)
