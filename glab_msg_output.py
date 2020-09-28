#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
import logging
import pathlib
import pandas as pd
from shutil import copyfile

import am_config as amc
from ampyutils import amutils, location, exeprogram
from glab import glab_constants as glc
from glab import glab_split_outfile, glab_parser_output, glab_parser_info, glab_statistics, glab_updatedb
from glab_plot import glab_plot_output_enu, glab_plot_output_stats

__author__ = 'amuls'


lst_centers = ['origin', 'wavg']
db_default_name = os.path.join(os.path.expanduser("~"), 'RxTURP', 'glab_output_db.csv')
lst_logging_choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        for log_action in log_actions:
            if log_action not in lst_logging_choices:
                raise argparse.ArgumentError(self, "log_actions must be in {choices!s}".format(choices=lst_logging_choices))
        setattr(namespace, self.dest, log_actions)


class scale_action(argparse.Action):
    def __call__(self, parser, namespace, scale_action, option_string=None):
        base_choices = [1, 2, 5]
        scale_choices = [.1, 1, 10, 100, 1000]
        all_choices = []
        for s in scale_choices:
            all_choices += [b * s for b in base_choices]
        if scale_action not in all_choices:
            raise argparse.ArgumentError(self, "scale_action must be in {choices!s}".format(choices=all_choices))
        setattr(namespace, self.dest, scale_action)


class center_action(argparse.Action):
    def __call__(self, parser, namespace, center_action, option_string=None):
        if center_action not in lst_centers:
            raise argparse.ArgumentError(self, "center_action must be in {choices!s}".format(choices=lst_centers))
        setattr(namespace, self.dest, center_action)


def treatCmdOpts(argv):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = amc.cBaseName + ' plots gLAB (v6) receiver position'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-r', '--rootdir', help='Root directory (default {:s})'.format(colored('.', 'green')), required=False, type=str, default='.')
    parser.add_argument('-f', '--file', help='gLAB compressed out file', required=True, type=str)
    # parser.add_argument('-r', '--resFile', help='RTKLib residuals file', type=str, required=False, default=None)
    # parser.add_argument('-m', '--marker', help='Geodetic coordinates (lat,lon,ellH) of reference point in degrees: 50.8440152778 4.3929283333 151.39179 for RMA, 50.93277777 4.46258333 123 for Peutie, default 0 0 0 means use mean position', nargs=3, type=str, required=False, default=["0", "0", "0"])
    parser.add_argument('-s', '--scale', help='display ENU plots with +/- this scale range (default 5m)', required=False, default=5, type=float, action=scale_action)
    parser.add_argument('-c', '--center', help='center ENU plots (Select from {!s})'.format('|'.join(lst_centers)), required=False, default=lst_centers[0], type=str, action=center_action)

    parser.add_argument('-d', '--db', help='CVS database (default {:s})'.format(colored(db_default_name, 'green')), required=False, default=db_default_name, type=str)

    parser.add_argument('-p', '--plots', help='displays interactive plots (default True)', action='store_true', required=False, default=False)
    # parser.add_argument('-o', '--overwrite', help='overwrite intermediate files (default False)', action='store_true', required=False)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (two of {choices:s}, default {choice:s})'.format(choices='|'.join(lst_logging_choices), choice=colored(' '.join(lst_logging_choices[3:5]), 'green')), nargs=2, required=False, default=lst_logging_choices[3:5], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.rootdir, args.file, args.scale, args.center, args.db, args.plots, args.logging


def check_arguments(logger: logging.Logger) -> int:
    """
    check_arguments checks the given arguments wether they are valid. return True or False
    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # check whether the given dir_root exist
    path = pathlib.Path(amc.dRTK['dir_root'])
    if not path.is_dir():
        logger.info('{func:s}: directory {root:s} does not exist'.format(root=colored(amc.dRTK['dir_root'], 'red'), func=cFuncName))
        return amc.E_DIR_NOT_EXIST
    else:  # change to directory
        os.chdir(path)

    # check whether the glab_compressed out file exists and is readable
    path = pathlib.Path(amc.dRTK['glab_cmp_out'])
    if not path.is_file():
        logger.info('{func:s}: file {file:s} does not exist'.format(file=colored(amc.dRTK['glab_cmp_out'], 'red'), func=cFuncName))
        return amc.E_FILE_NOT_EXIST

    # check whether the CVS database exists, if not check whether its directory exists, if not create
    path = pathlib.Path(amc.dRTK['dgLABng']['db'])
    if not path.is_file():
        logger.info('{func:s}: CVS database file {db:s} does not exist, will be created'.format(db=colored(amc.dRTK['dgLABng']['db'], 'green'), func=cFuncName))
        # check whether its directory exists
        if not path.parents[0].is_dir():
            path.parents[0].mkdir(parents=True)

    return amc.E_SUCCESS


def store_to_cvs(df: pd.DataFrame, ext: str, logger: logging.Logger, index: bool = True) -> str:
    """
    store the dataframe to a CSV file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    csv_name = amc.dRTK['glab_out'].split('.')[0] + '.' + ext

    # make dir if not exist
    dir_glabng = os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'])
    amutils.mkdir_p(dir_glabng)

    df.to_csv(os.path.join(dir_glabng, csv_name), index=index, header=True)

    # amutils.logHeadTailDataFrame(logger=logger, callerName=cFuncName, df=df, dfName=csv_name)
    logger.info('{func:s}: stored dataframe as csv file {csv:s}'.format(csv=colored(csv_name, 'yellow'), func=cFuncName))

    return csv_name


def main(argv) -> bool:
    """
    glabplotposn plots data from gLAB (v6) OUTPUT messages

    """
    amc.cBaseName = colored(os.path.basename(__file__), 'yellow')
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # limit float precision
    # encoder.FLOAT_REPR = lambda o: format(o, '.3f')
    # pd.options.display.float_format = "{:,.3f}".format

    # treat command line options
    dir_root, glab_cmp_out, scale_enu, center_enu, db_cvs, show_plot, log_levels = treatCmdOpts(argv)

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=dir_root, logLevels=log_levels)

    # store cli parameters
    amc.dRTK = {}
    amc.dRTK['dir_root'] = dir_root
    amc.dRTK['glab_cmp_out'] = glab_cmp_out

    # create sub dict for gLAB related info
    dgLABng = {}
    dgLABng['dir_glab'] = 'glabng'
    dgLABng['db'] = db_cvs

    amc.dRTK['dgLABng'] = dgLABng

    # check some arguments
    ret_val = check_arguments(logger=logger)
    if ret_val != amc.E_SUCCESS:
        sys.exit(ret_val)

    # open or create the database file for storing the statistics
    glab_updatedb.open_database(db_name=amc.dRTK['dgLABng']['db'], logger=logger)

    # glab_updatedb.db_update_line(db_name=amc.dRTK['dgLABng']['db'], line_id='2019,134', info_line='2019,134,new thing whole line for ', logger=logger)

    # get location of progs used
    amc.dRTK['progs'] = {}
    amc.dRTK['progs']['gunzip'] = location.locateProg('gunzip', logger)
    amc.dRTK['progs']['gzip'] = location.locateProg('gzip', logger)

    # uncompress the "out" file
    runGUNZIP = '{prog:s} -f -v {zip:s}'.format(prog=amc.dRTK['progs']['gunzip'], zip=os.path.join(amc.dRTK['dir_root'], amc.dRTK['glab_cmp_out']))
    logger.info('{func:s}: Uncompressing file {cmp:s}:\n{cmd:s}'.format(func=cFuncName, cmd=colored(runGUNZIP, 'green'), cmp=colored(amc.dRTK['glab_cmp_out'], 'green')))

    # run the program
    exeprogram.subProcessDisplayStdErr(cmd=runGUNZIP, verbose=True)

    # get name of uncompressed file
    amc.dRTK['glab_out'] = amc.dRTK['glab_cmp_out'][:-3]

    # split gLABs out file in parts
    glab_msgs = glc.dgLab['messages'][0:2]  # INFO & OUTPUT messages needed
    dglab_tmpfiles = glab_split_outfile.split_glab_outfile(msgs=glab_msgs, glab_outfile=amc.dRTK['glab_out'], logger=logger)

    # read in the INFO messages from INFO temp file
    amc.dRTK['INFO'] = glab_parser_info.parse_glab_info(glab_info=dglab_tmpfiles['INFO'], logger=logger)
    # write the identification to the database file for glabng output messages
    # glab_updatedb.db_update_line(db_name=amc.dRTK['dgLABng']['db'], line_id=amc.dRTK['INFO']['db_lineID'], info_line=amc.dRTK['INFO']['db_lineID'], logger=logger)

    # read in the OUTPUT messages from OUTPUT temp file
    df_output = glab_parser_output.parse_glab_output(glab_output=dglab_tmpfiles['OUTPUT'], logger=logger)
    # save df_output as CSV file
    amc.dRTK['dgLABng']['pos'] = store_to_cvs(df=df_output, ext='pos', logger=logger, index=False)

    # compress the stored CVS file
    runGZIP = '{prog:s} -f -v {zip:s}'.format(prog=amc.dRTK['progs']['gzip'], zip=os.path.join(amc.dRTK['dir_root'], amc.dRTK['dgLABng']['dir_glab'], amc.dRTK['dgLABng']['pos']))
    logger.info('{func:s}: Compressing file {cmp:s}:\n{cmd:s}'.format(func=cFuncName, cmd=colored(runGZIP, 'green'), cmp=colored(amc.dRTK['dgLABng']['pos'], 'green')))
    # run the program
    exeprogram.subProcessDisplayStdErr(cmd=runGZIP, verbose=True)

    # calculate statitics gLAB OUTPUT messages
    amc.dRTK['dgLABng']['stats'], dDB_crds = glab_statistics.statistics_glab_outfile(df_outp=df_output, logger=logger)

    for key, val in dDB_crds.items():
        glab_updatedb.db_update_line(db_name=amc.dRTK['dgLABng']['db'],
                                     line_id='{id:s},{crd:s}'.format(id=amc.dRTK['INFO']['db_lineID'], crd=key),
                                     info_line='{id:s},{val:s}'.format(id=amc.dRTK['INFO']['db_lineID'], val=val),
                                     logger=logger)

    # sort the glab_output_db
    glab_updatedb.db_sort(db_name=amc.dRTK['dgLABng']['db'], logger=logger)
    # sys.exit(2)

    # plot the gLABs OUTPUT messages
    # - position ENU and PDOP plots
    glab_plot_output_enu.plot_glab_position(dfCrd=df_output, scale=scale_enu, showplot=show_plot, logger=logger)
    # - scatter plot of EN per dop bind
    glab_plot_output_enu.plot_glab_scatter(dfCrd=df_output, scale=scale_enu, center=center_enu, showplot=show_plot, logger=logger)
    # - scatter plot of EN per dop bind (separate)
    glab_plot_output_enu.plot_glab_scatter_bin(dfCrd=df_output, scale=scale_enu, center=center_enu, showplot=show_plot, logger=logger)
    # - plot the DOP parameters
    glab_plot_output_enu.plot_glab_xdop(dfCrd=df_output, showplot=show_plot, logger=logger)
    # - plot the ENU box plots per DOP bin
    glab_plot_output_stats.plot_glab_statistics(df_dopenu=df_output[glc.dgLab['OUTPUT']['XDOP'] + glc.dgLab['OUTPUT']['dENU']], scale=scale_enu, showplot=show_plot, logger=logger)

    # report to the user
    logger.info('{func:s}: Project information =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    # sort the glab_output_db
    glab_updatedb.db_sort(db_name=amc.dRTK['dgLABng']['db'], logger=logger)

    # recompress the "out" file
    runGZIP = '{prog:s} -f -v {zip:s}'.format(prog=amc.dRTK['progs']['gzip'], zip=os.path.join(amc.dRTK['dir_root'], amc.dRTK['glab_out']))
    logger.info('{func:s}: Compressing file {cmp:s}:\n{cmd:s}'.format(func=cFuncName, cmd=colored(runGZIP, 'green'), cmp=colored(amc.dRTK['glab_out'], 'green')))
    # run the program
    exeprogram.subProcessDisplayStdErr(cmd=runGZIP, verbose=True)

    # store the json structure
    json_out = amc.dRTK['glab_out'].split('.')[0] + '.json'
    with open(json_out, 'w') as f:
        json.dump(amc.dRTK, f, ensure_ascii=False, indent=4, default=amutils.DT_convertor)
    logger.info('{func:s}: created json file {json:s}'.format(func=cFuncName, json=colored(json_out, 'green')))

    # copy temp log file to the YYDOY directory
    copyfile(log_name, os.path.join(amc.dRTK['dir_root'], '{obs:s}-{prog:s}'.format(obs=amc.dRTK['glab_out'].split('.')[0], prog='output.log')))
    os.remove(log_name)

    return amc.E_SUCCESS


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
