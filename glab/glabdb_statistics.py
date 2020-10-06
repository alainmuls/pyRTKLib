import sys
import os
from termcolor import colored
import logging
import pandas as pd
import json

from glab import glab_constants as glc
from ampyutils import amutils

__author__ = 'amuls'


def crd_statistics(crds: list, prcodes: list, df_crds: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    crd_statistics calculates the statistics for the slected coordinates based on available prcodes in dataframe.
    returns dict with statistical info per coordinate and per prcode selected
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: determining statistics for {crds:s}'.format(func=cFuncName, crds=colored(glc.dgLab['OUTPUT'][crds], 'green')))

    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_crds, dfName='df[{crds:s}]'.format(crds=crds))

    # dict for containingn the statistics
    dStats = {}

    # go over the crds
    for crd in glc.dgLab['OUTPUT'][crds]:
        dStats[crd] = {}
        # go over the prcodes
        for prcode in prcodes:
            logger.info('{func:s}: statistics for combination {crd:s} - {prcode:s}'.format(crd=crd, prcode=prcode, func=cFuncName))
            dStats[crd][prcode] = {}

            # select rows for prcode and for crd
            df_crd_prcode = df_crds[(df_crds['prcodes'].str.contains(prcode)) & (df_crds['crds'] == crd)]

            # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df_crd_prcode, dfName='df_crd_prcode'.format(crds=crds))

            dStats[crd][prcode]['mean'] = df_crd_prcode['mean'].mean()
            dStats[crd][prcode]['std'] = df_crd_prcode['mean'].std()
            dStats[crd][prcode]['max'] = df_crd_prcode['mean'].max()
            dStats[crd][prcode]['min'] = df_crd_prcode['mean'].min()

    logger.info('{func:s}: Statistics for {crd:s} =\n{json!s}'.format(crd=','.join(glc.dgLab['OUTPUT'][crds]), func=cFuncName, json=json.dumps(dStats, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    return dStats
