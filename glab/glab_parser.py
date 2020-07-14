import pandas as pd
from termcolor import colored
import sys
import os
import logging
import tempfile
import datetime as dt
import re
from datetime import datetime

from ampyutils import amutils
from glab import glab_constants as glc
import am_config as amc

__author__ = 'amuls'


def split_glab_outfile(glab_outfile: str, logger: logging.Logger) -> dict:
    """
    splitStatusFile splits the statistics file into the POS, SAT, CLK & VELACC parts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.debug('{func:s}: splitting gLABs file {statf:s}'.format(func=cFuncName, statf=glab_outfile))

    dgLab_tmpf = {}
    for glab_msg in glc.dgLab['messages']:
        dgLab_tmpf[glab_msg] = tempfile.NamedTemporaryFile(prefix='{:s}_'.format(glab_outfile), suffix='_{:s}'.format(glab_msg), delete=True)

        with open(dgLab_tmpf[glab_msg].name, 'w') as fTmp:
            fTmp.writelines(line for line in open(glab_outfile) if line.startswith(glab_msg))
            logger.info('{func:s}: size of {msg:s} file = {size:.2f} MB'.format(size=amutils.convert_unit(fTmp.tell(), amutils.SIZE_UNIT.MB), msg=glab_msg, func=cFuncName))

            # reset at start of file
            fTmp.seek(0)

    return dgLab_tmpf


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

    # # add UTM coordinates (drop zone info)
    # df_output['UTM.E'], df_output['UTM.N'], _, _ = utm.from_latlon(df_output['lat'].to_numpy(), df_output['lon'].to_numpy())

    # # add UTM difference with marker
    # df_output.loc[:, 'dUTM.E'] = df_output['UTM.E'].apply(lambda x: x - amc.dRTK['marker']['UTM.E'])
    # df_output.loc[:, 'dUTM.N'] = df_output['UTM.N'].apply(lambda x: x - amc.dRTK['marker']['UTM.N'])
    # df_output.loc[:, 'dellH'] = df_output['ellH'].apply(lambda x: x - amc.dRTK['marker']['ellH'])

    logger.info('{func:s}: df_output info\n{dtypes!s}'.format(dtypes=df_output.info(), func=cFuncName))
    amutils.printHeadTailDataFrame(df=df_output, name='OUTPUT section of {name:s}'.format(name=amc.dRTK['glab_out']))

    return df_output


def parse_glab_info(glab_info: str, logger: logging.Logger) -> dict:
    """
    parse_glab_info parses the INFO section from gLAB out file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Parsing gLab INFO section {file:s} ({info:s})'.format(func=cFuncName, file=glab_info.name, info=colored('be patient', 'red')))

    # read in all lines from gLAB INFO output
    with open(glab_info.name) as fh:
        lines = [line.rstrip() for line in fh]  # fh.readlines()  # [line.rstrip() for line in fh]

    # find the values for the dgLab['INFO'] we collect
    dInfo = {}
    for key, val in glc.dgLab['INFO'].items():
        line = [x for x in lines if x.startswith(val)]
        # store the found info
        # print(line)
        # print(type(line))
        if len(line) > 0:
            if ':' in line[0]:
                dInfo[key] = re.sub(" +", " ", line[0].partition(':')[2].strip())  # remove white spaces
            else:
                dInfo[key] = re.sub(" +", " ", line[0].partition(val)[2].strip())  # remove white spaces
        else:
            dInfo[key] = ''

    # print(dInfo)

    # print(len(lines))
    # for i in range(10):
    #     print(lines[i])

    return dInfo
