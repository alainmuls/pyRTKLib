import pandas as pd
from termcolor import colored
import sys
import os
import logging
import tempfile
import datetime as dt
import re
from datetime import datetime
import numpy as np
import json
import utm

from ampyutils import amutils
from glab import glab_constants as glc
import am_config as amc
from GNSS import wgs84

__author__ = 'amuls'


def split_glab_outfile(msgs: str, glab_outfile: str, logger: logging.Logger) -> dict:
    """
    splitStatusFile splits the statistics file into the POS, SAT, CLK & VELACC parts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: splitting gLABs out file {statf:s} ({info:s})'.format(func=cFuncName, statf=colored(glab_outfile, 'yellow'), info=colored('be patient', 'red')))

    # create the temporary files needed for this parsing
    dtmp_fnames = {}
    dtmp_fds = {}
    for glab_msg in msgs:
        dtmp_fnames[glab_msg] = tempfile.NamedTemporaryFile(prefix='{:s}_'.format(glab_outfile), suffix='_{:s}'.format(glab_msg), delete=True)
        dtmp_fds[glab_msg] = open(dtmp_fnames[glab_msg].name, 'w')

    # open gLABng '*.out' file for reading and start processing its lines parsing the selected messages
    with open(glab_outfile, 'r') as fd:
        line = fd.readline()
        while line:
            for glab_msg in msgs:
                if line.startswith(glab_msg):
                    dtmp_fds[glab_msg].write(line)
            line = fd.readline()

    # close the opened files
    for glab_msg in msgs:
        dtmp_fds[glab_msg].close()

        # return the dict with the temporary filenames created
    return dtmp_fnames


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


def parse_glab_info(glab_info: str, logger: logging.Logger) -> dict:
    """
    parse_glab_info parses the INFO section from gLAB out file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Parsing gLab INFO section {file:s} ({info:s})'.format(func=cFuncName, file=glab_info.name, info=colored('be patient', 'red')))

    # init class WGS84
    wgs_84 = wgs84.WGS84()

    # read in all lines from gLAB INFO output
    with open(glab_info.name) as fh:
        glab_info_lines = [line.rstrip() for line in fh]  # fh.readlines()  # [line.rstrip() for line in fh]

    # create a dictionary for storing/returning the information
    dInfo = {}

    # get the info about the input files (cfr glc.dgLab['parse']['files'])
    dInfo['files'] = parse_glab_info_files(glab_lines=glab_info_lines, dFiles=glc.dgLab['parse']['files'])
    # get the receiver information
    dInfo['rx'] = parse_glab_info_rx(glab_lines=glab_info_lines, dRx=glc.dgLab['parse']['rx'])

    # get the preprocessing output
    dInfo['pp'] = parse_glab_info_pp(glab_lines=glab_info_lines, dPP=glc.dgLab['parse']['pp'])

    # get info about th eModelling
    dInfo['model'] = parse_glab_info_model(glab_lines=glab_info_lines, dModel=glc.dgLab['parse']['model'])

    # report
    logger.info('{func:s}: Information summary =\n{json!s}'.format(func=cFuncName, json=json.dumps(dInfo, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    sys.exit(6)

    # find the values for the dgLab['INFO'] we collect
    for key, val in glc.dgLab['parse'].items():
        line = [x for x in glab_info_lines if x.startswith(val)]

        if len(line) > 0:
            # print('line = {!s}'.format(line))
            if ':' in line[0]:
                dInfo[key] = re.sub(" +", " ", line[0].partition(':')[2].strip())  # remove white spaces
            else:
                dInfo[key] = re.sub(" +", " ", line[0].partition(val)[2].strip())  # remove white spaces

            # treat the ECEF coordinates
            if key == 'rx_ecef':
                # convert cartesian position to geodetic coordiantes
                cart_crd = [float(w) for w in dInfo['rx_ecef'].split()[:3]]
                dInfo['rx_geod'] = wgs_84.ecef2lla(ecef=cart_crd)

        else:
            dInfo[key] = ''

    # check which GNSS are used and create a marker field in dInfo accoring to the found GNSSs
    list_of_marker = ['GPSN', 'GALI']
    dInfo['marker'] = ''

    # Check if all listed GNSSs are in dInfo['gnss_used']
    if all(([True if gnss[:3] in dInfo['gnss_used'] else False for gnss in list_of_marker])):
        dInfo['marker'] = 'COMB'
    else:
        for marker in list_of_marker:
            if marker[:3] in dInfo['gnss_used']:
                dInfo['marker'] = marker

    logger.info('{func:s}: Information summary =\n{json!s}'.format(func=cFuncName, json=json.dumps(dInfo, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return dInfo


def parse_glab_info_files(glab_lines: list, dFiles: dict) -> dict:
    """
    parse_glab_info_files parses the lines containg info about the input files
    """
    # get the info about the input files (cfr glc.dgLab['parse']['files'])
    dfile_info = {}
    for key, val in dFiles.items():
        line = [x for x in glab_lines if x.startswith(val)][0]

        # usefull file information is behind the colon ":"
        file_info = line.partition(':')[-1].strip()

        # store the info for corresponding key
        dfile_info[key] = [os.path.basename(fname) for fname in file_info.split(' ')]

    return dfile_info


def parse_glab_info_rx(glab_lines: list, dRx: dict) -> dict:
    """
    parse_glab_info_ex parses the lines containg info about the receiver
    """
    # get the info about the receiver(cfr glc.dgLab['parse']['rx'])
    drx_info = {}
    for key, val in dRx.items():
        line = [x for x in glab_lines if x.startswith(val)][0]

        # usefull file information is behind the colon ":"
        drx_info[key] = re.sub("\\s\\s+", " ", line.partition(':')[-1].strip())

    # return the info about the receiver
    return drx_info


def parse_glab_info_pp(glab_lines: list, dPP: dict) -> dict:
    """
    parse_glab_info_pp parses the lines containg info about the preprocessing
    """
    # get the info about the PP(cfr glc.dgLab['parse']['pp'])
    dpp_info = {}
    for key, val in dPP.items():
        # create subset of glab_lines for this key
        val_lines = [line for line in glab_lines if val in line and 'No' not in line]
        # print(val_lines)

        if len(val_lines) == 1:
            line = [x for x in glab_lines if x.startswith(val)][0]

            # usefull file information is behind the colon ":"
            dpp_info[key] = re.sub("\\s\\s+", " ", line.partition(':')[-1].strip())

            # treat the ECEF coordinates
            if key == 'rx_ecef':
                # init class WGS84
                wgs_84 = wgs84.WGS84()
                # convert cartesian position to geodetic coordiantes
                cart_crd = [float(w) for w in dpp_info[key].split()[:3]]
                dpp_info['rx_geod'] = wgs_84.ecef2lla(ecef=cart_crd)

        else:
            dpp_info[key] = {}
            if key == 'freqs':
                for gnss_line in val_lines:
                    GNSS = gnss_line[gnss_line.find('[') + 1: gnss_line.find(']')]
                    GNSS_freqs = re.sub("\\s\\s+", " ", gnss_line.partition(':')[-1].strip())

                    dpp_info[key][GNSS] = GNSS_freqs

            elif key == 'freqs_order':
                for freq_line in val_lines:
                    # find fisrt/last occurences of the symbol "|"
                    first_occ = freq_line.find('|')
                    last_occ = freq_line.rfind('|')

                    freqs_avail = freq_line[first_occ - 1: last_occ + 2]
                    freqs_svs = freq_line[last_occ + 2:].strip()

                    dpp_info[key][freqs_avail] = freqs_svs

    # return the preprocessing info
    return dpp_info


def parse_glab_info_model(glab_lines: list, dModel: dict) -> dict:
    """
    parse_glab_info_model parses the lines containg info about the modelling
    """
    # get the info about the PP(cfr glc.dgLab['parse']['pp'])
    dmodel_info = {}
    for key, val in dModel.items():
        # create subset of glab_lines for this key
        val_lines = [line for line in glab_lines if val in line]
        print(val_lines)

        if len(val_lines) == 1:
            line = [x for x in glab_lines if x.startswith(val)][0]

            # usefull file information is behind the colon ":"
            dmodel_info[key] = re.sub("\\s\\s+", " ", line.partition(':')[-1].strip())

        else:
            if key == 'tropo':
                # combine all into 1 value
                tropo_info = ''
                for line in val_lines:
                    tropo_info += re.sub("\\s\\s+", " ", line.partition(':')[-1].strip()) + ' '
                dmodel_info[key] = tropo_info.strip()

    return dmodel_info
