import pandas as pd
from termcolor import colored
import sys
import os
import logging
import json
import math

from ampyutils import amutils
from glab import glab_constants as glc
import am_config as amc
from GNSS import wgs84

__author__ = 'amuls'


def statistics_glab_outfile(df_outp: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    splitStatusFile splits the statistics file into the POS, SAT, CLK & VELACC parts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating statistics of OUTPUT messages'.format(func=cFuncName))

    # dictionary containing the statistics
    dStats = {}
    dStats['dop_bin'] = statistics_dopbin(df_dop_enu=df_outp[glc.dgLab['OUTPUT']['XDOP'] + glc.dgLab['OUTPUT']['dENU']], logger=logger)
    dStats['crd'] = statistics_coordinates(df_crd=df_outp[glc.dgLab['OUTPUT']['llh'] + glc.dgLab['OUTPUT']['dENU'] + glc.dgLab['OUTPUT']['sdENU']], logger=logger)

    return dStats


def statistics_dopbin(df_dop_enu: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    statistics_dopbin calculates the xDOP statistics for each xDOP bin
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating statistics of xDOP'.format(func=cFuncName))

    dStats_dop = {}

    amutils.printHeadTailDataFrame(df=df_dop_enu, name='df_dop_enu')

    # go over all PDOP bins and plot according to the markersBin defined
    for i in range(len(amc.dRTK['dop_bins']) - 1):
        bin_PDOP = 'bin{:d}-{:.0f}'.format(amc.dRTK['dop_bins'][i], amc.dRTK['dop_bins'][i + 1])
        logger.debug('{func:s}: bin_PDOP = {bin!s}'.format(bin=bin_PDOP, func=cFuncName))

        # create the dict for this PDOP interval
        dStats_dop[bin_PDOP] = {}

        # find the indices within this bin
        index4Bin = (df_dop_enu['PDOP'] > amc.dRTK['dop_bins'][i]) & (df_dop_enu['PDOP'] <= amc.dRTK['dop_bins'][i + 1])

        dStats_dop[bin_PDOP]['perc'] = index4Bin.mean()
        dStats_dop[bin_PDOP]['count'] = int(index4Bin.count() * index4Bin.mean())

        for denu in glc.dgLab['OUTPUT']['dENU']:
            dENU_stats = {}

            dENU_stats['mean'] = df_dop_enu.loc[index4Bin, denu].mean()
            dENU_stats['stddev'] = df_dop_enu.loc[index4Bin, denu].std()
            dENU_stats['min'] = df_dop_enu.loc[index4Bin, denu].min()
            dENU_stats['max'] = df_dop_enu.loc[index4Bin, denu].max()

            dStats_dop[bin_PDOP][denu] = dENU_stats

            logger.debug('{func:s}: in {bin:s} statistics for {crd:s} are {stat!s}'.format(func=cFuncName, bin=bin_PDOP, crd=denu, stat=dENU_stats))

    # report to the user
    logger.info('{func:s}: dStats_dop =\n{json!s}'.format(func=cFuncName, json=json.dumps(dStats_dop, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return dStats_dop


def statistics_coordinates(df_crd: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    statistics_coordinates calculates the coordinate statistics
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating coordinate statistics'.format(func=cFuncName))

    dStat_crd = {}

    # init class WGS84
    wgs_84 = wgs84.WGS84()

    amutils.printHeadTailDataFrame(df=df_crd, name='df_crd')

    for llh, sdENU in zip(glc.dgLab['OUTPUT']['llh'], glc.dgLab['OUTPUT']['sdENU']):
        dStat_crd['wavg_{:s}'.format(llh)] = amutils.wavg(df_crd, llh, sdENU)
        if llh == 'lat':
            dStat_crd['sdwavg_{:s}'.format(llh)] = math.radians(amutils.stddev(df_crd[llh], dStat_crd['wavg_lat'])) * wgs_84.a
        elif llh == 'lon':
            dStat_crd['sdwavg_{:s}'.format(llh)] = math.radians(amutils.stddev(df_crd[llh], dStat_crd['wavg_lat'])) * wgs_84.a * math.cos(math.radians(dStat_crd['wavg_lat']))
        else:
            dStat_crd['sdwavg_{:s}'.format(llh)] = amutils.stddev(df_crd[llh], dStat_crd['wavg_{:s}'.format(llh)])

    for dENU, sdENU in zip(glc.dgLab['OUTPUT']['dENU'], glc.dgLab['OUTPUT']['sdENU']):
        dStat_crd['wavg_{:s}'.format(dENU)] = amutils.wavg(df_crd, dENU, sdENU)
        dStat_crd['sdwavg_{:s}'.format(dENU)] = amutils.stddev(df_crd[dENU], dStat_crd['wavg_{:s}'.format(dENU)])

    # calculate statistics for the nuùeric values
    for crd in df_crd.columns:
        dStat_crd['mean_{:s}'.format(crd)] = df_crd[crd].mean()
        dStat_crd['std_{:s}'.format(crd)] = df_crd[crd].std()
        dStat_crd['max_{:s}'.format(crd)] = df_crd[crd].max()
        dStat_crd['min_{:s}'.format(crd)] = df_crd[crd].min()

    logger.info('{func:s}: amc.dRTK =\n{json!s}'.format(func=cFuncName, json=json.dumps(dStat_crd, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return dStat_crd
