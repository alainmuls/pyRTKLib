import os
import sys
from termcolor import colored
import json
from json import encoder
import logging
import subprocess
import tempfile

import am_config as amc
from ampyutils import amutils

__author__ = 'amuls'


def rnx_header_info(dTmpRnx: dict, logger: logging.Logger):
    """
    rnx_header_info extracts the basic hedaer info from the rinex file
    and stores it in a JSON structure
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create the CLI command for extracting header information into a JSON structure
    amc.dRTK['rnxchk'] = {}
    args4GFZRNX = [amc.dRTK['bin2rnx']['GFZRNX'], '-finp', dTmpRnx['obs'], '-meta', 'basic:json', '-fout', dTmpRnx['obs'] + '.json', '-f']
    logger.info('{func:s}: extracting RINEX observation header'.format(func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    with open(dTmpRnx['obs'] + '.json', 'r') as f:
        amc.dRTK['rnxchk']['obshdr'] = json.load(f)

    # report information to user
    logger.info('{func:s}: RINEX observation basic information'.format(func=cFuncName))
    logger.info('{func:s}:    Satellite systems: {satsys:s}'.format(satsys=amc.dRTK['rnxchk']['obshdr']['file']['satsys'], func=cFuncName))

    pass



