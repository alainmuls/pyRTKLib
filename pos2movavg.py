#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
import pandas as pd
import numpy as np
import utm
import logging
import geopy.distance

import am_config as amc
from rnx2rtkp import parse_rtkpos_file
from rnx2rtkp import rtklibconstants as rtkc
from ampyutils import amutils, df2excel
from plot import plot_utm

__author__ = 'amuls'


def treatCmdOpts(argv, ):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = amc.cBaseName + ' calculate weighted position (llh) & UTM from posn file'

    # create lists from dict values used as choices for arguments
    lstQuality = list(rtkc.dRTKQual.values())

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-p', '--pos', help='generated "rtk-pos" file', required=True, type=str)
    parser.add_argument('-r', '--rootdir', help='Root directory for campaign (default .)', required=False, type=str, default='.')
    parser.add_argument('-s', '--subdir', help='Sub directory of "rtk-pos" file (default .)', required=False, type=str, default='.')
    parser.add_argument('-q', '--quality', help='rnx2rtkp solution quality (default {:s})'.format(colored(lstQuality[4], 'green')), required=False, default=lstQuality[4], type=str, choices=lstQuality)
    parser.add_argument('-m', '--marker', help='Marker name', required=True, type=str)
    parser.add_argument('-c', '--campaign', help='Campaign name', required=True, type=str)
    parser.add_argument('-e', '--excel', help='create campaign excel file', required=False, action='store_true')

    parser.add_argument('-l', '--logging', help='specify logging level console/file (default {:s})'.format(colored('INFO DEBUG', 'green')), nargs=2, required=False, default=['INFO', 'DEBUG'], choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'])

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.pos, args.rootdir, args.subdir, args.quality, args.marker, args.campaign, args.excel, args.logging


def addRTKResult(logger: logging.Logger):
    """
    adds the result to campaign csv file
    """
    # write formatted output of result
    cFuncName = amc.cBaseName + ': ' + colored(sys._getframe().f_code.co_name, 'green')

    amc.dRTK['csvFile'] = os.path.join(amc.dRTK['rootDir'], '{campaign:s}.csv'.format(campaign=amc.dRTK['campaign']))

    # if campaign file exists, read in the data
    if os.access(amc.dRTK['csvFile'], os.R_OK):
        logger.info('{func:s}: reading campaign csv file {csv:s}'.format(func=cFuncName, csv=amc.dRTK['csvFile']))
        # read in the campaign data
        dfCampaign = pd.read_csv(amc.dRTK['csvFile'])
    else:
        # create an empty dataframe
        dfCampaign = pd.DataFrame(columns=['campaign', 'marker', 'date', 'start', 'end', 'rtkqual', '#obsTotal', '#obsQual', 'lat', 'lon', 'ellH', 'sdu', 'UTM.E', 'sde', 'UTM.N', 'sdn', 'UTM.Z', 'UTM.L', 'Ref_lat', 'Ref_lon', 'Ref_ellH', 'Ref_UTM.E', 'Ref_UTM.N', 'Ref_UTM.Z', 'Ref_UTM.L', 'Distance', 'DeltaH'])

    # check whether the current processing has been saved to csv file
    index = dfCampaign.loc[(dfCampaign['campaign'] == amc.dRTK['campaign']) &
                           (dfCampaign['marker'] == amc.dRTK['marker']) &
                           (dfCampaign['rtkqual'] == amc.dRTK['rtkqual'])].index
    # if index is not empty => delete dataframe current info
    if len(index) > 0:
        dfCampaign.drop(index, inplace=True)

    # calculate the slant distance to Reference if available
    try:
        crdWAvg = (amc.dRTK['WAVG']['lat'], amc.dRTK['WAVG']['lon'])
        crdRefPt = (amc.dRTK['RefPos'][0], amc.dRTK['RefPos'][1])

        distance = geopy.distance.vincenty(crdWAvg, crdRefPt).m
        DeltaH = amc.dRTK['WAVG']['ellH'] - amc.dRTK['RefPos'][2]

    except ValueError:
        distance = np.NaN
        DeltaH = np.NaN

    # add the new info to the csv file
    dfCampaign = dfCampaign.append(pd.Series([amc.dRTK['campaign'],
                                              amc.dRTK['marker'],
                                              amc.dRTK['obsStart'].strftime("%d/%m/%Y"),
                                              amc.dRTK['obsStart'].strftime('%H:%M:%S'),
                                              amc.dRTK['obsEnd'].strftime('%H:%M:%S'),
                                              amc.dRTK['rtkqual'],
                                              amc.dRTK['#obs'],
                                              amc.dRTK['#obsQual'],
                                              amc.dRTK['WAVG']['lat'],
                                              amc.dRTK['WAVG']['lon'],
                                              amc.dRTK['WAVG']['ellH'],
                                              amc.dRTK['WAVG']['sdellH'],
                                              amc.dRTK['WAVG']['UTM.E'],
                                              amc.dRTK['WAVG']['sdUTM.E'],
                                              amc.dRTK['WAVG']['UTM.N'],
                                              amc.dRTK['WAVG']['sdUTM.N'],
                                              amc.dRTK['WAVG']['UTM.Z'],
                                              amc.dRTK['WAVG']['UTM.L'],
                                              amc.dRTK['RefPos'][0],
                                              amc.dRTK['RefPos'][1],
                                              amc.dRTK['RefPos'][2],
                                              amc.dRTK['RefPosUTM'][0],
                                              amc.dRTK['RefPosUTM'][1],
                                              amc.dRTK['RefPosUTM'][2],
                                              amc.dRTK['RefPosUTM'][3],
                                              distance,
                                              DeltaH
                                             ], index=dfCampaign.columns), ignore_index=True)

    # sort the dataframe
    dfCampaign.sort_values(['campaign', 'date', 'rtkqual', 'marker'], ascending=[True, True, True, True], inplace=True)

    # format the output of data for importing in excel workbook
    # for col in ['ellH', 'UTM.E', 'UTM.N', 'Ref_ellH', 'Ref_UTM.N', 'Ref_UTM.E', 'Distance']:
    #     dfCampaign[col] = dfCampaign[col].map('{:.3f}'.format)
    # for col in ['lat', 'lon', 'Ref_lat', 'Ref_lon']:
    #     dfCampaign[col] = dfCampaign[col].map('{:.9f}'.format)

    # info logging for campaign
    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfCampaign, dfName='dfCampaign updated')

    # add campaign sheet write to excel workbook
    if amc.dRTK['excel']:
        df2excel.append_df_to_excel(filename=amc.dRTK['xlsName'], df=dfCampaign, sheet_name=amc.dRTK['campaign'], truncate_sheet=True, startrow=0, index=False, float_format="%.9f")
        logger.info('{func:s}: added sheet {sheet:s} to workbook {wb:s}'.format(func=cFuncName, sheet=amc.dRTK['campaign'], wb=amc.dRTK['xlsName']))

    # save the dataframe by overwriting the amc.dRTK['csvfile']
    dfCampaign.to_csv(amc.dRTK['csvFile'], index=None, header=True)


def main(argv):
    """
    pyRTKPlot adds UTM coordinates to output of rnx2rtkp.
    If 'stat' file is available, calculates xDOP values, and make plots of statictics

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # some options for diasplay of dataframes
    pd.set_option('display.max_columns', None)  # or 1000
    pd.set_option('display.max_rows', None)  # or 1000
    pd.set_option('display.max_colwidth', -1)  # or 199
    # limit float precision
    json.encoder.FLOAT_REPR = lambda o: format(o, '.3f')

    # treat command line options
    posFile, rootDir, subDir, rtkqual, marker, campaign, excel, logLevels = treatCmdOpts(argv)

    # store cli parameters
    amc.dRTK = {}
    amc.dRTK['rootDir'] = rootDir
    amc.dRTK['subDir'] = subDir
    amc.dRTK['posDir'] = os.path.join(rootDir, subDir)
    amc.dRTK['posFile'] = posFile
    amc.dRTK['rtkqual'] = rtkqual
    amc.dRTK['marker'] = marker
    amc.dRTK['campaign'] = campaign
    amc.dRTK['excel'] = excel

    # get th enumeric vale for this quality
    amc.dRTK['iQual'] = [key for key, value in rtkc.dRTKQual.items() if value == amc.dRTK['rtkqual']][0]

    if amc.dRTK['excel']:
        amc.dRTK['xlsName'] = os.path.join(amc.dRTK['rootDir'], '{pos:s}.xlsx'.format(pos=amc.dRTK['campaign']))

    # create logging for better debugging
    logger, logname = amc.createLoggers(baseName=os.path.basename(__file__), dir=amc.dRTK['posDir'], logLevels=logLevels)

    # change to selected directory if exists
    if not os.path.exists(amc.dRTK['posDir']):
        logger.error('{func:s}: directory {dir:s} does not exists'.format(func=cFuncName, dir=colored(amc.dRTK['posDir'], 'red')))
        sys.exit(amc.E_DIR_NOT_EXIST)
    else:
        os.chdir(amc.dRTK['posDir'])
        print(amc.dRTK['posDir'])
        print(type(amc.dRTK['posDir']))
        print('{func:s}: changed to dir {dir!s}'.format(func=cFuncName, dir=colored(amc.dRTK['posDir'], 'green')))

    # check wether pos and stat file are present, else exit
    if not os.access(os.path.join(amc.dRTK['posDir'], amc.dRTK['posFile']), os.R_OK):
        logger.error('{func:s}: file {pos:s} is not accessible'.format(func=cFuncName, pos=os.path.join(amc.dRTK['posDir'], amc.dRTK['posFile'])))
        sys.exit(amc.E_FILE_NOT_EXIST)

    # read the position file into a dataframe and add dUTM coordinates
    dfPos = parse_rtkpos_file.parsePosFile(logger=logger)

    # get the indices according to the position mode
    idx = dfPos.index[dfPos['Q'] == amc.dRTK['iQual']]

    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfPos.loc[idx], dfName='{posf:s}'.format(posf=amc.dRTK['posFile']))

    # determine statistics for the requested quality mode
    logger.info('{func:s}: stats are\n{stat!s}'.format(func=cFuncName, stat=dfPos.loc[idx][['lat', 'lon', 'ellH', 'UTM.E', 'UTM.N']].describe()))
    # add weighted average for th erequested quality of position
    llh = ['lat', 'lon', 'ellH', 'UTM.E', 'UTM.N']
    dSDenu = ['sdn', 'sde', 'sdu', 'sdn', 'sde']

    dWAVG = {}

    for values in zip(llh, dSDenu):
        dWAVG[values[0]] = parse_rtkpos_file.wavg(group=dfPos.loc[idx], avg_name=values[0], weight_name=values[1])
    # calculate the stddev of the weighted average
    for crd in llh[2:]:
        # print('crd = {!s}'.format(crd))
        dWAVG['sd{crd:s}'.format(crd=crd)] = parse_rtkpos_file.stddev(dfPos.loc[idx][crd], dWAVG[(crd)])
        # print(dWAVG)
        # print('{crd:s} = {sd:.3f}'.format(crd=crd, sd=dWAVG['sd{crd:s}'.format(crd=crd)]))

    # get UTM coordiantes/zone for weigted average
    dWAVG['UTM.E'], dWAVG['UTM.N'], dWAVG['UTM.Z'], dWAVG['UTM.L'] = utm.from_latlon(dWAVG['lat'], dWAVG['lon'])
    amc.dRTK['WAVG'] = dWAVG

    logger.info('{func:s}: weighted averages: {wavg!s}'.format(func=cFuncName, wavg=dWAVG))

    amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=dfPos, dfName='{posf:s}'.format(posf=amc.dRTK['posFile']))

    # create UTM plot
    plot_utm.plot_utm_ellh(dRtk=amc.dRTK, dfUTM=dfPos, logger=logger, showplot=True)

    # add results to campaign file
    addRTKResult(logger)

    # write to csv file
    csvName = os.path.join(amc.dRTK['posDir'], '{pos:s}.csv'.format(pos=amc.dRTK['posFile']))
    dfPos.to_csv(csvName, index=None, header=True)

    # add sheet write to excel workbook
    if amc.dRTK['excel']:
        sheetName = '{pos:s}-{qual:s}'.format(pos=os.path.splitext(os.path.basename(amc.dRTK['posFile']))[0], qual=amc.dRTK['rtkqual'])
        df2excel.append_df_to_excel(filename=amc.dRTK['xlsName'], df=dfPos, sheet_name=sheetName, truncate_sheet=True, startrow=0, index=False, float_format="%.9f")
        logger.info('{func:s}: added sheet {sheet:s} to workbook {wb:s}'.format(func=cFuncName, sheet=sheetName, wb=amc.dRTK['xlsName']))

    logger.info('{func:s}: amc.dRTK =\n{settings!s}'.format(func=cFuncName, settings=amc.dRTK))

    # # TEST OK
    # lats = np.array([-31.373988106, -31.373988805])
    # lons = np.array([-64.440817783, -64.440817762])
    # result = utm.from_latlon(lats, lons)
    # print(lats)
    # print(lons)
    # print(result)
    # # EOF TEST OK


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
