import logging
from termcolor import colored
import sys
import os
import io
import pandas as pd
import inspect

# global used variables by passing as module
dRTK = {}  # contains settings maily put by CLI arguments
dGNSSs = {}  # dict with SatSyst and numeric value for lookup
dSettings = {}  # dict containing the values to be used in the template
dConv = {}  # dict for the conversion from Binary to RINEX
cBaseName = ''  # colored version of main script
dLogLevel = {'CRITICAL': 50, 'ERROR': 40, 'WARNING': 30, 'INFO': 20, 'DEBUG': 10, 'NOTSET': 0}

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


def createLoggers(baseName: str, dir=dir, logLevels: str = ['INFO', 'DEBUG']) -> logging.Logger:
    """
    create logging for python
    """
    pyLogger = logging.getLogger(os.path.splitext(baseName)[0])
    pyLogger.setLevel(level=logging.DEBUG)

    # create file handler which logs even debug messages
    fh = logging.FileHandler('{:s}.log'.format(os.path.splitext(baseName)[0]), mode='w')
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

    return pyLogger


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
