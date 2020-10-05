from termcolor import colored
import sys
import os
import logging
import re
import json
from typing import Tuple

from ampyutils import amutils
from glab import glab_constants as glc
from GNSS import wgs84

__author__ = 'amuls'


def parse_glab_info(glab_info: str, logger: logging.Logger) -> dict:
    """
    parse_glab_info parses the INFO section from gLAB out file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Parsing gLab INFO section {file:s} ({info:s})'.format(func=cFuncName, file=glab_info.name, info=colored('be patient', 'red')))

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
    dInfo['pp'] = parse_glab_info_preprocessing(glab_lines=glab_info_lines, dPP=glc.dgLab['parse']['pp'])

    # get info about th eModelling
    dInfo['model'] = parse_glab_info_model(glab_lines=glab_info_lines, dModel=glc.dgLab['parse']['model'])

    # get info about gLABs Filter
    dInfo['filter'], marker, dInfo['rx']['gnss'] = parse_glab_info_filter(glab_lines=glab_info_lines, dFilter=glc.dgLab['parse']['filter'])

    if dInfo['rx']['marker'] != 'GPRS':
        dInfo['rx']['marker'] = marker

    # get info about th summary
    dInfo['summary'] = parse_glab_info_summary(glab_lines=glab_info_lines, dSummary=glc.dgLab['parse']['summary'])

    # report
    logger.info('{func:s}: Information summary =\n{json!s}'.format(func=cFuncName, json=json.dumps(dInfo, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    # create common start of line for logging into database
    svs_codes = dInfo['filter']['meas'][:dInfo['filter']['meas'].index(' StdDev')]
    dInfo['db_lineID'] = '{YYYY:04d},{DOY:03d},{gnss:s},{marker:s},{meas:s}'.format(YYYY=dInfo['summary']['Year'], DOY=dInfo['summary']['DoY'], gnss=dInfo['filter']['gnss'], marker=dInfo['rx']['marker'], meas=svs_codes)

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


def parse_glab_info_preprocessing(glab_lines: list, dPP: dict) -> dict:
    """
    parse_glab_info_preprocessing parses the lines containg info about the preprocessing
    """
    # get the info about the PP(cfr glc.dgLab['parse']['pp'])
    dpp_info = {}
    for key, val in dPP.items():
        # create subset of glab_lines for this key
        val_lines = [line for line in glab_lines if val in line and 'No' not in line]

        if len(val_lines) == 1:
            line = val_lines[0]

            if ':' in line:
                # usefull file information is behind the colon ":"
                dpp_info[key] = re.sub("\\s\\s+", " ", line.partition(':')[-1].strip())
            else:
                if key == 'freqs_order':
                    dpp_info[key] = {}

                    # find fisrt/last occurences of the symbol "|"
                    first_occ = line.find('|')
                    last_occ = line.rfind('|')

                    freqs_avail = line[first_occ - 1: last_occ + 2]
                    freqs_svs = line[last_occ + 2:].strip()

                    dpp_info[key][freqs_avail] = freqs_svs

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

        if len(val_lines) == 1:
            # usefull file information is behind the colon ":"
            dmodel_info[key] = re.sub("\\s\\s+", " ", val_lines[0].partition(':')[-1].strip())

        else:
            if key == 'tropo':
                # combine all into 1 value
                tropo_info = ''
                for line in val_lines:
                    tropo_info += re.sub("\\s\\s+", " ", line.partition(':')[-1].strip()) + ' '
                dmodel_info[key] = tropo_info.strip()

    return dmodel_info


def parse_glab_info_filter(glab_lines: list, dFilter: dict) -> Tuple[dict, str, str]:
    """
    parse_glab_info_filter parses the lines containg info about the Filterling
    """
    # get the info about the PP(cfr glc.dgLab['parse']['pp'])
    dFilter_info = {}
    for key, val in dFilter.items():
        # create subset of glab_lines for this key
        val_lines = [line for line in glab_lines if val in line]

        if len(val_lines) == 1:
            line = val_lines[0]

            if ':' in line:
                # usefull file information is behind the colon ":"
                dFilter_info[key] = re.sub("\\s\\s+", " ", line.partition(':')[-1].strip())

            if key == 'meas':
                # split the found FILTER info on spaces

                syst_meas = dFilter_info[key].split(' ')

                # regex for checking the systems we have
                re_meas = r'[A-Z]\d\d-\d\d'

                dFilter_info['gnss'] = ''
                for info in syst_meas:
                    if re.match(re_meas, info):
                        dFilter_info['gnss'] += info[0]

        else:  # more than 1 element in 'val_lines'
            if key == 'meas':
                dFilter_info[key] = ''
                dFilter_info['gnss'] = ''
                # regex for checking the systems we have
                re_meas = r'[A-Z]\d\d-\d\d'

                for line in val_lines:
                    if ':' in line:
                        if len(dFilter_info[key]) > 0:
                            dFilter_info[key] += ', '
                        # usefull file information is behind the colon ":"
                        dFilter_info[key] += re.sub("\\s\\s+", " ", line.partition(':')[-1].strip())

                    syst_meas = line.split(' ')
                    for info in syst_meas:
                        if re.match(re_meas, info) and info[0] not in dFilter_info['gnss']:
                            dFilter_info['gnss'] += info[0]

    # lookup corresponding MARKER name and GNSS
    marker = glc.dgLab['GNSS'][dFilter_info['gnss']]['marker']
    gnss = glc.dgLab['GNSS'][dFilter_info['gnss']]['gnss']

    return dFilter_info, marker, gnss


def parse_glab_info_summary(glab_lines: list, dSummary: dict) -> dict:
    """
    parse_glab_info_summary parses the lines containg info about the Filterling
    """
    # get the info about the PP(cfr glc.dgLab['parse']['pp'])
    dSummary_info = {}

    summary_line = [line for line in glab_lines if dSummary in line][0]
    posn_colon = summary_line.find('Lon:')
    info_line = summary_line[posn_colon:]

    list_tmp = info_line.split()[::2]
    list_of_keys = [key.strip(':') for key in list_tmp]
    list_of_str_values = info_line.split()[1::2]

    list_of_values = [RepresentsNumber(value) for value in list_of_str_values]

    # create dictionary of key:values
    dSummary_info = dict(zip(list_of_keys, list_of_values))

    return dSummary_info


def RepresentsNumber(s: str):
    try:
        int(s)
        return int(s)
    except ValueError:
        try:
            float(s)
            return float(s)
        except ValueError:
            return s
