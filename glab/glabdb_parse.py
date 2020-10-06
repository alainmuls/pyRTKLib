import sys
import os
from termcolor import colored
import logging
import tempfile

import am_config as amc

__author__ = 'amuls'


def db_parse_gnss_codes(db_name: str, crd_types: list, logger: logging.Logger) -> str:
    """
    db_parse_gnss_codes parses the database file and keeps the lines according to a specific GNSSs and prcodes, keeping only the lines specified in the crd list
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: parsing database file {file:s}'.format(func=cFuncName, file=colored(db_name, 'green')))

    # open the CSV glabdb file and check each line
    tmp_csvdb_name = os.path.join(tempfile.gettempdir(), tempfile.NamedTemporaryFile(suffix=".csv").name)
    # print(tmp_csvdb_name)

    # determine the keys for the temp dict to create
    keys = ['year', 'doy', 'gnss', 'marker', 'prcode', 'crd_type']

    with open(amc.dRTK['options']['glab_db']) as inf, open(tmp_csvdb_name, 'w') as outf:
        for line in inf:
            # print(line.split(','))

            dLine = dict(zip(keys, line.split(',')))

            # check whether this line is to be selected
            if check_vailidity_line(line_dict=dLine, crd_types=crd_types):
                outf.write(line)

    return tmp_csvdb_name


def check_vailidity_line(line_dict: dict, crd_types: list) -> bool:
    """
    check_vailidity_line checks whether this line is within the selected YYYY/DOYs, GNSS, prcodes and Coordinate type
    """
    # check on year
    if not int(line_dict['year']) == amc.dRTK['options']['yyyy']:
        return False

    # check DOY in selected range
    if not int(line_dict['doy']) in range(amc.dRTK['options']['doy_begin'], amc.dRTK['options']['doy_last'] + 1):
        return False

    # check for selected GNSS
    if not line_dict['gnss'] in amc.dRTK['options']['gnsss']:
        return False

    # check for the marker (if calue is not None)
    if amc.dRTK['options']['markers'][0] != 'None':
        if not line_dict['marker'] in amc.dRTK['options']['markers']:
            return False

    # check for the prcode
    if not any(prcode in line_dict['prcode'] for prcode in amc.dRTK['options']['prcodes']):
        return False

    # check for the crd_type
    if not any(crd_type in line_dict['crd_type'] for crd_type in crd_types):
        return False

    return True

# with open('test.txt', 'r') as inf, open('test1.txt', 'w') as outf:
#     for line in inf:
#         line = line.strip()
#         if line:
#             try:
#                 outf.write(str(int(line, 16)))
#                 outf.write('\n')
#             except ValueError:
#                 print("Could not parse '{0}'".format(line))
