import sys
import os
import tempfile
from datetime import datetime
import logging
from termcolor import colored
import json

import am_config as amc
from ampyutils import amutils

__author__ = 'amuls'


def rnxobs_header_info(logger: logging.Logger):
    """
    rnxobs_header_info extracts the basic hedaer info from the rinex file
    and stores it in a JSON structure
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    rnx_obs_file = os.path.join(amc.dRTK['rnx_dir'], amc.dRTK['rnx_obs'])
    json_file = os.path.join(tempfile.gettempdir(), 'rnx_obs.json')

    args4GFZRNX = [amc.dRTK['bin']['GFZRNX'], '-finp', rnx_obs_file, '-meta', 'basic:json', '-fout', json_file, '-f']
    logger.info('{func:s}: extracting RINEX observation header from {rnx_obs:s}'.format(rnx_obs=rnx_obs_file, func=cFuncName))
    amutils.run_subprocess(sub_proc=args4GFZRNX, logger=logger)

    with open(json_file, 'r') as f:
        dObsHdr = json.load(f)

    # collect time info
    dTimes = {}
    dTimes['DT'] = datetime.strptime(dObsHdr['data']['epoch']['first'][:-1], '%Y %m %d %H %M %S.%f')
    dTimes['date'] = dTimes['DT'].date()
    dTimes['doy'] = dTimes['DT'].timetuple().tm_yday
    dTimes['year'] = dTimes['DT'].timetuple().tm_year
    dTimes['yy'] = dTimes['year'] % 100

    # keep this info
    amc.dRTK['DT'] = dTimes

    logger.info('{func:s}: dObsHdr =\n{json!s}'.format(func=cFuncName, json=json.dumps(dObsHdr, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    print(dObsHdr['site']['name'])
    # remove the temporary json file
    os.remove(json_file)
