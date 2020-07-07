import matplotlib.pyplot as plt
from matplotlib import dates
from matplotlib import colors as mpcolors
from termcolor import colored
import numpy as np
import os
import pandas as pd
import sys
import logging
from typing import Tuple

from ampyutils import amutils
from plot import plot_utils
import am_config as amc
from glab import glab_constants as glc

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

__author__ = 'amuls'


def plot_glab_position(df_outp: pd.DataFrame, logger: logging.Logger):
    """
    plot_glab_position plots the position difference wrt to Nominal a priori position
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # plot the ENU difference xwrt nominal initial position and display the standard deviation, xDOP
    for dCrd, sdCrd in zip(glc.dgLab['OUTPUT']['plot']['dENU'], glc.dgLab['OUTPUT']['plot']['sdENU']):
        print('{:s} {:s}'.format(dCrd, sdCrd))
