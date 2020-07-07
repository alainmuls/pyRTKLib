import pandas as pd
from termcolor import colored
import sys
import os
import logging
import utm
import tempfile
import datetime as dt

from ampyutils import amutils
from glab import glab_constants
import am_config as amc

__author__ = 'amuls'


def split_glab_outfile(glab_outfile: str, logger: logging.Logger) -> dict:
    """
    splitStatusFile splits the statistics file into the POS, SAT, CLK & VELACC parts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.debug('{func:s}: splitting gLABs file {statf:s}'.format(func=cFuncName, statf=glab_outfile))

    # read in the glab_outfile and split it into its parts (stored in temporary files)
    glab_msgs = ('INFO', 'OUTPUT', 'SATSEL', 'MEAS', 'MODEL', 'FILTER')
    dglab = {}

    for glab_msg in glab_msgs:
        dglab[glab_msg] = tempfile.NamedTemporaryFile(prefix='{:s}_'.format(glab_outfile), suffix='_{:s}'.format(glab_msg), delete=True)

        with open(dglab[glab_msg].name, 'w') as fTmp:
            fTmp.writelines(line for line in open(glab_outfile) if line.startswith(glab_msg))
            logger.info('{func:s}: size of {msg:s} file = {size:d}'.format(size=fTmp.tell(), msg=glab_msg, func=cFuncName))

            # reset at start of file
            fTmp.seek(0)

    return dglab


def parse_glab_output(glab_output: tempfile._TemporaryFileWrapper, logger: logging.Logger) -> pd.DataFrame:
    """
    parse_glab_output parses the OUTPUT section of the glab out file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Parsing gLab OUTPUT section {file:s} ({info:s})'.format(func=cFuncName, file=glab_output.name, info=colored('be patient', 'red')))

    # read gLABs OUTPUT into dataframe
    df_output = pd.read_csv(glab_output.name, header=None, delim_whitespace=True, usecols=[*range(1, 11), *range(20, len(glab_constants.dgLab['OUTPUT']['columns']))])

    # name the colmuns
    df_output.columns = glab_constants.dgLab['OUTPUT']['use_cols']

    # tranform time column to python datetime.time
    df_output['Time'] = df_output['Time'].apply(lambda x: dt.datetime.strptime(x, '%H:%M:%S.%f').time())

    # # add UTM coordinates (drop zone info)
    # df_output['UTM.E'], df_output['UTM.N'], _, _ = utm.from_latlon(df_output['lat'].to_numpy(), df_output['lon'].to_numpy())

    # # add UTM difference with marker
    # df_output.loc[:, 'dUTM.E'] = df_output['UTM.E'].apply(lambda x: x - amc.dRTK['marker']['UTM.E'])
    # df_output.loc[:, 'dUTM.N'] = df_output['UTM.N'].apply(lambda x: x - amc.dRTK['marker']['UTM.N'])
    # df_output.loc[:, 'dellH'] = df_output['ellH'].apply(lambda x: x - amc.dRTK['marker']['ellH'])

    logger.info('{func:s}: df_output info\n{dtypes!s}'.format(dtypes=df_output.info(), func=cFuncName))
    amutils.printHeadTailDataFrame(df=df_output, name='OUTPUT section of {name:s}'.format(name=amc.dRTK['glab_out']))

    return df_output
