import pandas as pd
from termcolor import colored
import sys
import os
import logging
import tempfile
import datetime as dt
from datetime import datetime
import numpy as np
import utm

from ampyutils import amutils
from glab import glab_constants as glc
import am_config as amc

__author__ = 'amuls'


def make_datetime(year: int, doy: int, t: datetime.time) -> dt.datetime:
    """
    converts the YYYY, DoY and Time to a datetime
    """
    return dt.datetime.strptime('{!s} {!s} {!s}'.format(year, doy, t.strftime('%H:%M:%S')), '%Y %j %H:%M:%S')


def parse_glab_output(glab_output: tempfile._TemporaryFileWrapper, logger: logging.Logger) -> pd.DataFrame:
    """
    parse_glab_output parses the OUTPUT section of the glab out file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Parsing gLab OUTPUT section {file:s} ({info:s})'.format(func=cFuncName, file=glab_output.name, info=colored('be patient', 'red')))

    # read gLABs OUTPUT into dataframe (cropping cartesian colmuns)
    df_output = pd.read_csv(glab_output.name, header=None, delim_whitespace=True, usecols=[*range(1, 11), *range(20, len(glc.dgLab['OUTPUT']['columns']))])

    # name the colmuns
    df_output.columns = glc.dgLab['OUTPUT']['use_cols']

    # tranform time column to python datetime.time and add a DT column
    df_output['Time'] = df_output['Time'].apply(lambda x: dt.datetime.strptime(x, '%H:%M:%S.%f').time())
    df_output['DT'] = df_output.apply(lambda x: make_datetime(x['Year'], x['DoY'], x['Time']), axis=1)

    # find gaps in the data by comparing to mean value of difference in time
    df_output['dt_diff'] = df_output['DT'].diff(1)
    dtMean = df_output['dt_diff'].mean()

    # look for it using location indexing
    df_output.loc[df_output['dt_diff'] > dtMean, '#SVs'] = np.nan
    df_output.loc[df_output['dt_diff'] > dtMean, 'PDOP'] = np.nan

    # add UTM coordinates
    df_output['UTM.E'], df_output['UTM.N'], _, _ = utm.from_latlon(df_output['lat'].to_numpy(), df_output['lon'].to_numpy())

    logger.info('{func:s}: df_output info\n{dtypes!s}'.format(dtypes=df_output.info(), func=cFuncName))
    amutils.printHeadTailDataFrame(df=df_output, name='OUTPUT section of {name:s}'.format(name=amc.dRTK['glab_out']), index=False)

    return df_output
