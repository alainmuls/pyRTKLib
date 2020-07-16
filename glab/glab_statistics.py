import pandas as pd
from termcolor import colored
import sys
import os
import logging
import json

from ampyutils import amutils
from glab import glab_constants as glc
import am_config as amc

__author__ = 'amuls'


def statistics_glab_outfile(df_outp: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    splitStatusFile splits the statistics file into the POS, SAT, CLK & VELACC parts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating statistics of OUTPUT messages'.format(func=cFuncName))

    # dictionary containing the statistics
    dStats = {}
    dStats['DOP'] = statistics_xDOP(df_dop_enu=df_outp[glc.dgLab['OUTPUT']['XDOP'] + glc.dgLab['OUTPUT']['dENU']], logger=logger)

    return dStats


def statistics_xDOP(df_dop_enu: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    statistics_xDOP calculates the xDOP statistics for each xDOP bin
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating statistics of xDOP'.format(func=cFuncName))

    dXDOP_stats = {}

    amutils.printHeadTailDataFrame(df=df_dop_enu, name='df_dop_enu')

    # go over all PDOP bins and plot according to the markersBin defined
    for i in range(len(amc.dRTK['dop_bins']) - 1):
        bin_PDOP = 'bin{:d}-{:.0f}'.format(amc.dRTK['dop_bins'][i], amc.dRTK['dop_bins'][i + 1])
        logger.debug('{func:s}: bin_PDOP = {bin!s}'.format(bin=bin_PDOP, func=cFuncName))

        # create the dict for this PDOP interval
        dXDOP_stats[bin_PDOP] = {}

        # find the indices within this bin
        index4Bin = (df_dop_enu['PDOP'] > amc.dRTK['dop_bins'][i]) & (df_dop_enu['PDOP'] <= amc.dRTK['dop_bins'][i + 1])

        dXDOP_stats[bin_PDOP]['perc'] = index4Bin.mean()
        dXDOP_stats[bin_PDOP]['count'] = int(index4Bin.count() * index4Bin.mean())

        for denu in glc.dgLab['OUTPUT']['dENU']:
            dENU_stats = {}

            dENU_stats['mean'] = df_dop_enu.loc[index4Bin, denu].mean()
            dENU_stats['stddev'] = df_dop_enu.loc[index4Bin, denu].std()
            dENU_stats['min'] = df_dop_enu.loc[index4Bin, denu].min()
            dENU_stats['max'] = df_dop_enu.loc[index4Bin, denu].max()

            dXDOP_stats[bin_PDOP][denu] = dENU_stats

            logger.debug('{func:s}: in {bin:s} statistics for {crd:s} are {stat!s}'.format(func=cFuncName, bin=bin_PDOP, crd=denu, stat=dENU_stats))

    # report to the user
    logger.info('{func:s}: dXDOP_stats =\n{json!s}'.format(func=cFuncName, json=json.dumps(dXDOP_stats, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return dXDOP_stats
