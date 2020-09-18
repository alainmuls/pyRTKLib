import pandas as pd
from termcolor import colored
import sys
import os
import logging
import json
import math
import numpy as np
from typing import Tuple

from ampyutils import amutils
from glab import glab_constants as glc
from GNSS import wgs84

__author__ = 'amuls'


def statistics_glab_outfile(df_outp: pd.DataFrame, logger: logging.Logger) -> Tuple[dict, dict]:
    """
    splitStatusFile splits the statistics file into the POS, SAT, CLK & VELACC parts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating statistics of OUTPUT messages'.format(func=cFuncName))

    # dictionary containing the statistics
    dStats = {}
    dStats['dop_bin'] = statistics_dopbin(df_dop_enu=df_outp[glc.dgLab['OUTPUT']['XDOP'] + glc.dgLab['OUTPUT']['dENU'] + glc.dgLab['OUTPUT']['sdENU']], logger=logger)
    dStats['crd'] = statistics_coordinates(df_crd=df_outp[glc.dgLab['OUTPUT']['llh'] + glc.dgLab['OUTPUT']['dENU'] + glc.dgLab['OUTPUT']['sdENU'] + glc.dgLab['OUTPUT']['UTM']], logger=logger)

    # print(dStats.keys())
    # print(dStats['crd'].keys())
    # print(dStats['crd']['dN0'].keys())
    # create the dNEU information to store in the glabng output database
    dDB_crd = {}
    for crd in glc.dgLab['OUTPUT']['dENU']:
        dDB_crd[crd] = '{crd:s},'.format(crd=crd)
        dDB_crd[crd] += '{mean:+.3f},'.format(mean=dStats['crd'][crd]['mean'])
        dDB_crd[crd] += '{std:+.3f},'.format(std=dStats['crd'][crd]['std'])
        dDB_crd[crd] += '{max:+.3f},'.format(max=dStats['crd'][crd]['max'])
        dDB_crd[crd] += '{min:+.3f},'.format(min=dStats['crd'][crd]['min'])
        # print('crd from glc = {crd:s} - {info:s}'.format(crd=crd, info=dDB_crd[crd]))

        for i, (dop_min, dop_max) in enumerate(zip(glc.dop_bins[:-1], glc.dop_bins[1:])):
            bin_interval = 'bin{:d}-{:.0f}'.format(dop_min, dop_max)
            # print(bin_interval)

            dDB_crd[crd] += '{mean:+.3f},'.format(mean=dStats['dop_bin'][bin_interval][crd]['mean'])
            dDB_crd[crd] += '{std:+.3f},'.format(std=dStats['dop_bin'][bin_interval][crd]['std'])
            dDB_crd[crd] += '{max:+.3f},'.format(max=dStats['dop_bin'][bin_interval][crd]['max'])
            dDB_crd[crd] += '{min:+.3f}'.format(min=dStats['dop_bin'][bin_interval][crd]['min'])

            if i < len(glc.dop_bins[:-1]) - 1:
                dDB_crd[crd] += ','

    # create the llh information to store in the glabng output database
    for i, crd in enumerate(glc.dgLab['OUTPUT']['llh']):
        dDB_crd[crd] = '{crd:s},'.format(crd=crd)
        if crd == 'ellh':
            dDB_crd[crd] += '{mean:+.3f},'.format(mean=dStats['crd'][crd]['mean'])
            dDB_crd[crd] += '{std:+.3f},'.format(std=dStats['crd'][crd]['std'])
            dDB_crd[crd] += '{max:+.3f},'.format(max=dStats['crd'][crd]['max'])
            dDB_crd[crd] += '{min:+.3f}'.format(min=dStats['crd'][crd]['min'])
        else:
            dDB_crd[crd] += '{mean:+.9f},'.format(mean=dStats['crd'][crd]['mean'])
            dDB_crd[crd] += '{std:+.9f},'.format(std=dStats['crd'][crd]['std'])
            dDB_crd[crd] += '{max:+.9f},'.format(max=dStats['crd'][crd]['max'])
            dDB_crd[crd] += '{min:+.9f}'.format(min=dStats['crd'][crd]['min'])

    # create the llh information to store in the glabng output database
    for i, crd in enumerate(glc.dgLab['OUTPUT']['UTM']):
        dDB_crd[crd] = '{crd:s},'.format(crd=crd)
        dDB_crd[crd] += '{mean:+.3f},'.format(mean=dStats['crd'][crd]['mean'])
        dDB_crd[crd] += '{std:+.3f},'.format(std=dStats['crd'][crd]['std'])
        dDB_crd[crd] += '{max:+.3f},'.format(max=dStats['crd'][crd]['max'])
        dDB_crd[crd] += '{min:+.3f}'.format(min=dStats['crd'][crd]['min'])

    # print('crd from glc = {crd:s} - {info:s}'.format(crd=crd, info=dDB_crd[crd]))

    return dStats, dDB_crd


def statistics_dopbin(df_dop_enu: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    statistics_dopbin calculates the xDOP statistics for each xDOP bin
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating statistics of xDOP'.format(func=cFuncName))

    dStats_dop = {}

    amutils.printHeadTailDataFrame(df=df_dop_enu, name='df_dop_enu')

    # go over all PDOP bins and plot according to the markersBin defined
    for i in range(len(glc.dop_bins) - 1):
        bin_PDOP = 'bin{:d}-{:.0f}'.format(glc.dop_bins[i], glc.dop_bins[i + 1])
        logger.debug('{func:s}: bin_PDOP = {bin!s}'.format(bin=bin_PDOP, func=cFuncName))

        # create the dict for this PDOP interval
        dStats_dop[bin_PDOP] = {}

        # find the indices within this bin
        index4Bin = (df_dop_enu['PDOP'] > glc.dop_bins[i]) & (df_dop_enu['PDOP'] <= glc.dop_bins[i + 1])

        dStats_dop[bin_PDOP]['perc'] = index4Bin.mean()
        dStats_dop[bin_PDOP]['count'] = int(index4Bin.count() * index4Bin.mean())

        for dENU, sdENU in zip(glc.dgLab['OUTPUT']['dENU'], glc.dgLab['OUTPUT']['sdENU']):
            dENU_stats = {}

            dENU_stats['wavg'] = amutils.wavg(df_dop_enu.loc[index4Bin], dENU, sdENU)
            dENU_stats['sdwavg'] = amutils.stddev(df_dop_enu.loc[index4Bin, dENU], dENU_stats['wavg'])
            dENU_stats['mean'] = df_dop_enu.loc[index4Bin, dENU].mean()
            dENU_stats['median'] = df_dop_enu.loc[index4Bin, dENU].median()
            dENU_stats['std'] = df_dop_enu.loc[index4Bin, dENU].std()
            dENU_stats['min'] = df_dop_enu.loc[index4Bin, dENU].min()
            dENU_stats['max'] = df_dop_enu.loc[index4Bin, dENU].max()

            # add for this crd dENU
            dStats_dop[bin_PDOP][dENU] = dENU_stats

            logger.debug('{func:s}: in {bin:s} statistics for {crd:s} are {stat!s}'.format(func=cFuncName, bin=bin_PDOP, crd=dENU, stat=dENU_stats))

    # report to the user
    logger.info('{func:s}: dStats_dop =\n{json!s}'.format(func=cFuncName, json=json.dumps(dStats_dop, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return dStats_dop


def statistics_coordinates(df_crd: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    statistics_coordinates calculates the coordinate statistics
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: calculating coordinate statistics'.format(func=cFuncName))

    # init class WGS84
    wgs_84 = wgs84.WGS84()

    amutils.printHeadTailDataFrame(df=df_crd, name='df_crd', index=False)
    dStat = {}
    for crd in (glc.dgLab['OUTPUT']['llh'] + glc.dgLab['OUTPUT']['dENU'] + glc.dgLab['OUTPUT']['UTM']):
        dStat[crd] = {}

    # make sure to have the wavg for latitude since it is used for converting the stddev of geodetic coordinates into meter
    dStat['lat']['wavg'] = amutils.wavg(df_crd, 'lat', 'dN0')
    for llh, sdENU in zip(glc.dgLab['OUTPUT']['llh'], glc.dgLab['OUTPUT']['sdENU']):
        dStat[llh]['wavg'] = amutils.wavg(df_crd, llh, sdENU)
        if llh == 'lat':
            dStat[llh]['sdwavg'] = math.radians(amutils.stddev(df_crd[llh], dStat['lat']['wavg'])) * wgs_84.a
        elif llh == 'lon':
            dStat[llh]['sdwavg'] = math.radians(amutils.stddev(df_crd[llh], dStat['lat']['wavg'])) * wgs_84.a * math.cos(math.radians(dStat['lat']['wavg']))
        else:
            dStat[llh]['sdwavg'] = amutils.stddev(df_crd[llh], dStat[llh]['wavg'])

    for dENU, sdENU in zip(glc.dgLab['OUTPUT']['dENU'], glc.dgLab['OUTPUT']['sdENU']):
        dStat[dENU]['wavg'] = amutils.wavg(df_crd, dENU, sdENU)
        dStat[dENU]['sdwavg'] = amutils.stddev(df_crd[dENU], dStat[dENU]['wavg'])

    for dUTM, sdENU in zip(glc.dgLab['OUTPUT']['UTM'], glc.dgLab['OUTPUT']['sdENU'][:2]):
        dStat[dUTM]['wavg'] = amutils.wavg(df_crd, dUTM, sdENU)
        dStat[dUTM]['sdwavg'] = amutils.stddev(df_crd[dUTM], dStat[dENU]['wavg'])

    # calculate statistics for the nuùeric values
    for crd in (glc.dgLab['OUTPUT']['llh'] + glc.dgLab['OUTPUT']['dENU'] + glc.dgLab['OUTPUT']['UTM']):
        dStat[crd]['mean'] = df_crd[crd].mean()
        dStat[crd]['median'] = df_crd[crd].median()
        dStat[crd]['std'] = df_crd[crd].std()
        dStat[crd]['max'] = df_crd[crd].max()
        dStat[crd]['min'] = df_crd[crd].min()

        # results of gLAB kalman filter
        dStat[crd]['kf'] = df_crd[crd].iloc[-1]
        try:
            dStat[crd]['sdkf'] = df_crd['s{:s}'.format(crd[:2])].iloc[-1]
        except KeyError:
            dStat[crd]['sdkf'] = np.nan

    logger.info('{func:s}: OUTPUT statistics information =\n{json!s}'.format(func=cFuncName, json=json.dumps(dStat, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return dStat
