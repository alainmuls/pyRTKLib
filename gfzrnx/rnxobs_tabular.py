import sys
import os
from datetime import datetime
import logging
from termcolor import colored
import pandas as pd

import am_config as amc
from ampyutils import amutils

__author__ = 'amuls'


def read_obs_tabular(gnss: str, logger: logging.Logger) -> pd.DataFrame:
    """
    read_obs_tabular reads the observation data into a dataframe
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # check that th erequested OBSTAB file is present
    gnss_obstab = os.path.join(amc.dRTK['gfzrnxDir'], amc.dRTK['rnx']['gnss'][gnss]['marker'], amc.dRTK['rnx']['gnss'][gnss]['obstab'])

    # df = pd.read_csv('gnss_obstab')
    logger.info('{func:s}: reading observation tabular file {obstab:s}'.format(obstab=colored(gnss_obstab, 'green'), func=cFuncName))
    try:
        df = pd.read_csv(gnss_obstab, parse_dates=[['DATE', 'TIME']], delim_whitespace=True)
    except FileNotFoundError as e:
        print('{func:s}: Error = {err!s}'.format(err=e, func=cFuncName))
        sys.exit(amc.E_FILE_NOT_EXIST)

    return df

