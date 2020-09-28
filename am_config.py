import logging
import os
import sys
import io
import pandas as pd
import inspect
import tempfile
from typing import Tuple
from termcolor import colored
import json

from ampyutils import amutils


# global used variables by passing as module
dRTK = {}  # contains settings maily put by CLI arguments
dGNSSs = {}  # dict with SatSyst and numeric value for lookup
dSettings = {}  # dict containing the values to be used in the template
dConv = {}  # dict for the conversion from Binary to RINEX
cBaseName = ''  # colored version of main script
dLogLevel = {'CRITICAL': 50,
             'ERROR': 40,
             'WARNING': 30,
             'INFO': 20,
             'DEBUG': 10,
             'NOTSET': 0}

# dictionary of GNSS systems
dGNSSs = {'G': 'GPS NavSTAR',
          'R': 'Glonass',
          'E': 'Galileo',
          'S': 'SBAS',
          'C': 'Beidou',
          'J': 'QZSS',
          'I': 'IRNSS',
          'M': 'Combined EG'}

dRnx_ext = {'E': {'obs': 'O', 'nav': 'E'},
            'G': {'obs': 'O', 'nav': 'N'},
            'M': {'obs': 'O', 'nav': 'P'}}

# exit codes
E_SUCCESS = 0
E_FILE_NOT_EXIST = 1
E_NOT_IN_PATH = 2
E_UNKNOWN_OPTION = 3
E_TIME_PASSED = 4
E_WRONG_OPTION = 5
E_SIGNALTYPE_MISMATCH = 6
E_DIR_NOT_EXIST = 7
E_INVALID_ARGS = 8
E_SBF2RIN_ERRCODE = 9
E_OSERROR = 10
E_FAILURE = 99


def createLoggers(baseName: str, dir=dir, logLevels: str = ['INFO', 'DEBUG']) -> Tuple[logging.Logger, str]:
    """
    create logging for python and returns temporary file name
    """
    pyLogger = logging.getLogger(os.path.splitext(baseName)[0])
    pyLogger.setLevel(level=logging.DEBUG)

    # create file handler which logs even debug messages
    tmp_log_name = os.path.join(tempfile.gettempdir(), tempfile.NamedTemporaryFile(suffix=".log").name)
    fh = logging.FileHandler('{:s}'.format(tmp_log_name), mode='w')

    fh.setLevel(dLogLevel[logLevels[1]])

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(dLogLevel[logLevels[0]])

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the pyLogger
    pyLogger.addHandler(fh)
    pyLogger.addHandler(ch)

    return pyLogger, tmp_log_name


def logDataframeInfo(df: pd.DataFrame, dfName: str, callerName: str, logger: logging.Logger):
    """
    lofDataframeInfo logs the info of a dataframe from log level DEBUG
    """
    buf = io.StringIO()
    df.info(buf=buf)
    logger.debug('{func:s}: {name:s} info = {info!s}'.format(func=callerName, name=dfName, info=buf.getvalue()))
    buf.truncate(0)


def lineno():
    """Returns the current line number in our program."""
    return inspect.currentframe().f_back.f_lineno


def get_title_info(logger: logging.Logger) -> Tuple[str, str]:
    """
    get_title_info gets basic info from the gLab['INFO'] dict for the plot
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: get information for reporting on plot'.format(func=cFuncName))

    # # make title for plot
    # date = datetime.strptime(amc.dRTK['INFO']['epoch_first'][:10], '%d/%m/%Y')
    # time_first = datetime.strptime(amc.dRTK['INFO']['epoch_first'][11:19], '%H:%M:%S')
    # time_last = datetime.strptime(amc.dRTK['INFO']['epoch_last'][11:19], '%H:%M:%S')
    # gnss_used = amc.dRTK['INFO']['gnss_used']
    # gnss_meas = amc.dRTK['INFO']['meas']
    # obs_file = os.path.basename(amc.dRTK['INFO']['obs'])
    # nav_file = os.path.basename(amc.dRTK['INFO']['nav'])
    # rx_geod = amc.dRTK['INFO']['rx_geod']

    # extract from collected information
    dInfo = dRTK['INFO']

    # print('Info = {!s}'.format(dInfo))
    logger.info('{func:s}: dInfo =\n{json!s}'.format(func=cFuncName, json=json.dumps(dInfo, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    marker = dInfo['rx']['marker']
    gnss = dInfo['rx']['gnss']

    date = '{day:02d}/{month:02d}/{year:04d}'.format(day=dInfo['summary']['Day'], month=dInfo['summary']['Month'], year=dInfo['summary']['Year'])
    WkTOW = '{week:04d}/{doy:03d}'.format(week=dInfo['summary']['GPSWeek'], doy=dInfo['summary']['DoY'])

    obs_file = dInfo['files']['obs'][0]
    nav_file = dInfo['files']['nav'][0]
    for i in range(1, len(dInfo['files']['obs'])):
        obs_file += dInfo['files']['obs'][i]
    for i in range(1, len(dInfo['files']['nav'])):
        nav_file += dInfo['files']['nav'][i]

    meas = dInfo['filter']['meas']
    ref_clk = dInfo['filter']['ref_clk']

    tropo = dInfo['model']['tropo']
    iono = dInfo['model']['iono']

    mask = dInfo['pp']['mask']
    geod_crd = dInfo['pp']['rx_geod']

    plot_title = '{posf:s}: {marker:s} - {obs_date:s} ({wktow:s})'.format(posf=obs_file, marker=marker, obs_date=date, wktow=WkTOW)
    proc_info = '{GNSS:s} - {meas:s}\nIono {iono:s} - Tropo {tropo:s} - RefClk {clk:s} - mask {mask:s}'.format(GNSS=gnss, meas=meas, iono=iono, tropo=tropo, clk=ref_clk, mask=mask)

    return plot_title, proc_info, geod_crd
