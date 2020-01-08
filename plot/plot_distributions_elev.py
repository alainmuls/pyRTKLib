import matplotlib
import matplotlib.pyplot as plt
from termcolor import colored
import numpy as np
import os
import pandas as pd
import sys
import logging
from matplotlib.ticker import FixedLocator
from matplotlib.gridspec import GridSpec
from matplotlib import dates

from pandas.plotting import register_matplotlib_converters
from ampyutils import amutils
from plot import plot_utils

register_matplotlib_converters()

__author__ = 'amuls'


def plot_elev_distribution(dRtk: dict, df: pd.DataFrame, obsName: str, logger: logging.Logger, showplot: bool = False):
    """
    plot_elev_distribution plots the distribution of CN0 or PRres as function of elevation bins
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: creating {obs:s} distribution plot'.format(obs=obsName, func=cFuncName))

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df, dfName=obsName)

    sys.exit(333)
