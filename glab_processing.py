#!/usr/bin/env python

import sys
import os
import argparse
from termcolor import colored
import json
import logging
import pathlib
from shutil import move
from string import Template

import am_config as amc
from ampyutils import amutils, location, exeprogram

__author__ = 'amuls'


lst_rnx_id = ['COMB', 'GPRS']
lst_gnsss = ['E', 'G']
lst_prcodes = ['C1C', 'C1W', 'C2L', 'C2W', 'C2W', 'C5Q', 'C1A', 'C6A']

lst_rxtypes = ['ASTX', 'BEGP']
dir_igs = os.path.join(os.path.expanduser("~"), 'RxTURP/BEGPIOS/igs')

lst_logging_choices = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'NOTSET']

glab_template = os.path.join(os.path.expanduser("~"), 'RxTURP/BEGPIOS', 'glab_kinematic.tmpl')


class logging_action(argparse.Action):
    def __call__(self, parser, namespace, log_actions, option_string=None):
        for log_action in log_actions:
            if log_action not in lst_logging_choices:
                raise argparse.ArgumentError(self, "log_actions must be in {logoptions!s}".format(logoptions='|'.join(lst_logging_choices)))
        setattr(namespace, self.dest, log_actions)


class doy_action(argparse.Action):
    def __call__(self, parser, namespace, doy, option_string=None):
        if doy not in range(1, 366):
            raise argparse.ArgumentError(self, "day-of-year must be in [1...366]")
        setattr(namespace, self.dest, doy)


class rxtype_action(argparse.Action):
    def __call__(self, parser, namespace, rxtype, option_string=None):
        if rxtype not in lst_rxtypes:
            raise argparse.ArgumentError(self, 'rxtype is one of {rxtypes:s}'.format(rxtypes='|'.join(lst_rxtypes)))
        setattr(namespace, self.dest, rxtype)


class marker_action(argparse.Action):
    def __call__(self, parser, namespace, marker, option_string=None):
        if marker not in lst_rnx_id:
            raise argparse.ArgumentError(self, 'marker is one of {markers:s}'.format(markers='|'.join(lst_rnx_id)))
        setattr(namespace, self.dest, marker)


class gnss_action(argparse.Action):
    def __call__(self, parser, namespace, gnsss, option_string=None):
        for gnss in gnsss:
            if gnss not in lst_gnsss:
                raise argparse.ArgumentError(self, 'select GNSS(s) out of {gnsss:s}'.format(gnsss='|'.join(lst_gnsss)))
        setattr(namespace, self.dest, gnsss)


class cutoff_action(argparse.Action):
    def __call__(self, parser, namespace, cutoff, option_string=None):
        if cutoff not in range(0, 90):
            raise argparse.ArgumentError(self, 'cutoff must be within [0..90] degrees')
        setattr(namespace, self.dest, cutoff)


class prcode_action(argparse.Action):
    def __call__(self, parser, namespace, prcodes, option_string=None):
        for prcode in prcodes:
            if prcode not in lst_prcodes:
                raise argparse.ArgumentError(self, 'prcode is one of {prcodes:s}'.format(prcodes='|'.join(lst_prcodes)))
        setattr(namespace, self.dest, prcodes)


def treatCmdOpts(argv):
    """
    Treats the command line options

    :param argv: the options
    :type argv: list of string
    """
    baseName = os.path.basename(__file__)
    amc.cBaseName = colored(baseName, 'yellow')

    helpTxt = amc.cBaseName + ' processes gLAB (v6) receiver position based on a template configuration file'

    # create the parser for command line arguments
    parser = argparse.ArgumentParser(description=helpTxt)
    parser.add_argument('-i', '--igsdir', help='Root IGS directory (default {igs:s}))'.format(igs=colored(dir_igs, 'green')), required=False, type=str, default=dir_igs)

    parser.add_argument('-r', '--rxtype', help='Receiver type (one of {choices:s} (default {choice:s}))'.format(choices='|'.join(lst_rxtypes), choice=colored(lst_rxtypes[0], 'green')), default=lst_rxtypes[0], required=False, type=str, action=rxtype_action)
    parser.add_argument('-m', '--marker', help='marker name (4 chars, one of {markers:s}, default {marker:s})'.format(markers='|'.join(lst_rnx_id), marker=colored(lst_rnx_id[0], 'green')), type=str, required=False, default=lst_rnx_id[0], action=marker_action)

    parser.add_argument('-y', '--year', help='Year (4 digits)', required=True, type=int)
    parser.add_argument('-d', '--doy', help='day-of-year [1..366]', required=True, type=int, action=doy_action)

    parser.add_argument('-g', '--gnss', help='select GNSS(s) to use (out of {gnsss:s}, default {gnss:s})'.format(gnsss='|'.join(lst_gnsss), gnss=colored(lst_gnsss[0], 'green')), default=lst_gnsss[0], type=str, required=False, action=gnss_action, nargs='+')

    parser.add_argument('-p', '--prcodes', help='select from {prcodes:s} (default to {prcode:s})'.format(prcodes='|'.join(lst_prcodes), prcode=colored(lst_prcodes[0], 'green')), required=False, type=str, default=lst_prcodes[0], action=prcode_action, nargs='+')

    parser.add_argument('-c', '--cutoff', help='cutoff angle (default {cutoff:s})'.format(cutoff=colored('5 deg', 'green')), required=False, default=5, type=int, action=cutoff_action)

    parser.add_argument('-t', '--template', help='glab template file (default {tmpl:s})'.format(tmpl=colored(glab_template, 'green')), required=False, type=str, default=glab_template)

    parser.add_argument('-l', '--logging', help='specify logging level console/file (two of {choices:s}, default {choice:s})'.format(choices='|'.join(lst_logging_choices), choice=colored(' '.join(lst_logging_choices[3:5]), 'green')), nargs=2, required=False, default=lst_logging_choices[3:5], action=logging_action)

    # drop argv[0]
    args = parser.parse_args(argv[1:])

    # return arguments
    return args.rxtype, args.igsdir, args.marker, args.year, args.doy, args.gnss, args.prcodes, args.cutoff, args.template, args.logging


def check_arguments(logger: logging.Logger) -> int:
    """
    check_arguments checks the given arguments wether they are valid. return True or False
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # check whether the given dir_rnx exist
    # root directory for processing
    amc.dRTK['proc'] = {}

    amc.dRTK['proc']['dir_rnx'] = os.path.join(os.path.expanduser("~"), 'RxTURP/BEGPIOS', amc.dRTK['options']['rxtype'], 'rinex', '{yy:s}{doy:03d}'.format(yy=str(amc.dRTK['options']['year'])[-2:], doy=amc.dRTK['options']['doy']))
    path = pathlib.Path(amc.dRTK['proc']['dir_rnx'])
    if not path.is_dir():
        logger.info('{func:s}: root directory {root:s} does not exist'.format(root=colored(amc.dRTK['proc']['dir_rnx'], 'red'), func=cFuncName))
        return amc.E_DIR_NOT_EXIST
    else:  # change to directory
        os.chdir(path)

    # check whether the given IGS dir exist
    amc.dRTK['proc']['dir_igs'] = os.path.join(amc.dRTK['options']['igs_root'], '{yy:s}{doy:03d}'.format(yy=str(amc.dRTK['options']['year'])[-2:], doy=amc.dRTK['options']['doy']))
    path = pathlib.Path(amc.dRTK['proc']['dir_igs'])
    if not path.is_dir():
        logger.info('{func:s}: IGS directory {igs:s} does not exist'.format(igs=colored(amc.dRTK['proc']['dir_igs'], 'red'), func=cFuncName))
        return amc.E_DIR_NOT_EXIST

    # path to the glab directory, create it of not existing
    amc.dRTK['proc']['dir_glab'] = os.path.join(amc.dRTK['proc']['dir_rnx'], 'glab')
    path = pathlib.Path(amc.dRTK['proc']['dir_glab'])
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=True)
        logger.info('{func:s}: Created glab directory {glab:s} does not exist'.format(glab=colored(amc.dRTK['proc']['dir_glab'], 'green'), func=cFuncName))

    # check whether the template file exists
    path = pathlib.Path(amc.dRTK['options']['template'])
    if not path.is_file():
        logger.info('{func:s}: gLAB template file {tmpl:s} does not exist'.format(tmpl=colored(amc.dRTK['options']['template'], 'red'), func=cFuncName))
        return amc.E_FILE_NOT_EXIST

    # create the RINEX obs name and check whether it exists
    amc.dRTK['proc']['cmp_obs'] = '{marker:s}{doy:03d}0.{yy:s}D.Z'.format(marker=amc.dRTK['options']['marker'], yy=str(amc.dRTK['options']['year'])[-2:], doy=amc.dRTK['options']['doy'])

    # determine the options for GNSS and codes / freqs
    amc.dRTK['proc']['marker'] = amc.dRTK['options']['marker']
    amc.dRTK['proc']['gnss'] = [gnss for gnss in amc.dRTK['options']['gnss']]
    amc.dRTK['proc']['cmp_nav'] = []
    for gnss in amc.dRTK['proc']['gnss']:
        # determine the navigation files used (currently using the IGS NAV files - should be changed)
        amc.dRTK['proc']['cmp_nav'].append('BRUX00BEL_R_{year:04d}{doy:03d}0000_01D_{gnss:s}N.rnx.gz'.format(year=amc.dRTK['options']['year'], doy=amc.dRTK['options']['doy'], gnss=gnss))

    # get the codes used and corresponding frequency numbers
    amc.dRTK['proc']['codes'] = [code for code in amc.dRTK['options']['prcodes']]
    amc.dRTK['proc']['freqs'] = [prcode[1:2] for prcode in amc.dRTK['proc']['codes']]

    # name for glab output file
    amc.dRTK['proc']['glab_out'] = '{marker:s}-{gnss:s}-{codes:s}.out'.format(marker=amc.dRTK['proc']['marker'], gnss=''.join(amc.dRTK['proc']['gnss']), codes='-'.join(amc.dRTK['proc']['codes']))
    amc.dRTK['proc']['glab_cfg'] = amc.dRTK['proc']['glab_out'][:-3] + 'cfg'

    return amc.E_SUCCESS


def uncompress_rnx_files(logger: logging.Logger):
    """
    uncompress_rnx_files uncompresses RINEX OBS & NAV files
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # uncompress the RINEX OBS file
    runCRZ2RNX = '{prog:s} -f {crz:s}'.format(prog=amc.dRTK['progs']['crz2rnx'], crz=os.path.join(amc.dRTK['proc']['dir_rnx'], amc.dRTK['proc']['cmp_obs']))
    logger.info('{func:s}: Running:\n{cmd:s}'.format(func=cFuncName, cmd=colored(runCRZ2RNX, 'green')))

    # run the program
    exeprogram.subProcessDisplayStdErr(cmd=runCRZ2RNX, verbose=True)

    # get name of uncompressed file
    amc.dRTK['proc']['obs'] = amc.dRTK['proc']['cmp_obs'][:-3] + 'O'

    # check if this decompressed file exists
    path = pathlib.Path(os.path.join(amc.dRTK['proc']['dir_rnx'], amc.dRTK['proc']['obs']))
    if not path.is_file():
        logger.info('{func:s}: Failed creating decompressed RINEX observation file {obs:s}'.format(obs=colored(amc.dRTK['proc']['obs'], 'green'), func=cFuncName))

    # decompress allnavigation files
    amc.dRTK['proc']['nav'] = []
    for cmp_nav in amc.dRTK['proc']['cmp_nav']:
        runGUNZIP = '{prog:s} -f {zip:s}'.format(prog=amc.dRTK['progs']['gunzip'], zip=os.path.join(amc.dRTK['proc']['dir_igs'], cmp_nav))
        logger.info('{func:s}: Running:\n{cmd:s}'.format(func=cFuncName, cmd=colored(runGUNZIP, 'green')))

        # run the program
        exeprogram.subProcessDisplayStdErr(cmd=runGUNZIP, verbose=True)

        # get name of uncompressed file
        amc.dRTK['proc']['nav'].append(cmp_nav[:-3])

        # check if this decompressed file exists
        path = pathlib.Path(os.path.join(amc.dRTK['proc']['dir_igs'], amc.dRTK['proc']['nav'][-1]))
        if not path.is_file():
            logger.info('{func:s}: Failed creating decompressed RINEX navigation file {nav:s}'.format(nav=colored(amc.dRTK['proc']['nav'], 'green'), func=cFuncName))


def cleanup_rnx_files(logger: logging.Logger):
    """
    cleanup_rnx_files cleans up the uncompressed RINEX obs & nav files (restoring original state)
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # remove obs rinex file used
    logger.info('{func:s}: removal of OBS file {obs:s}'.format(obs=amc.dRTK['proc']['obs'], func=cFuncName))
    os.remove(os.path.join(amc.dRTK['proc']['dir_rnx'], amc.dRTK['proc']['obs']))

    # recompress the navigation files
    for nav_file in amc.dRTK['proc']['nav']:
        runGZIP = '{prog:s} -f {zip:s}'.format(prog=amc.dRTK['progs']['gzip'], zip=os.path.join(amc.dRTK['proc']['dir_igs'], nav_file))
        logger.info('{func:s}: compressing {nav:s} file by:\n{cmd:s}'.format(nav=nav_file, func=cFuncName, cmd=colored(runGZIP, 'green')))
        # run the program
        exeprogram.subProcessDisplayStdErr(cmd=runGZIP, verbose=True)


def create_session_template(logger: logging.Logger):
    """
    create_session_template creates the configuration file for glabng
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # create dict used for replacing the template keywords
    dTemplate = {}
    dTemplate['CMP_OBS_FILE'] = os.path.join(amc.dRTK['proc']['dir_rnx'], amc.dRTK['proc']['obs'])
    dTemplate['CMP_NAV_FILES'] = ''
    for nav_file in amc.dRTK['proc']['nav']:
        dTemplate['CMP_NAV_FILES'] += ' ' + os.path.join(amc.dRTK['proc']['dir_igs'], nav_file)
    dTemplate['CUTOFF_ANGLE'] = amc.dRTK['options']['cutoff']
    dTemplate['GNSS'] = ''.join(amc.dRTK['proc']['gnss'])
    if len(amc.dRTK['proc']['codes']) == 1:
        dTemplate['PRCODES'] = '-'.join(amc.dRTK['proc']['codes'])
    else:
        dTemplate['PRCODES'] = 'PC' + ''.join(amc.dRTK['proc']['freqs']) + '-' + '-'.join(amc.dRTK['proc']['codes'])
    dTemplate['GLAB_OUT'] = os.path.join(amc.dRTK['proc']['dir_glab'], amc.dRTK['proc']['glab_out'])

    # report to the user
    # logger.info('{func:s}: creating config file {cfg:s} using:\n{json!s}'.format(cfg=colored(amc.dRTK['proc']['glab_cfg'], 'green'), func=cFuncName, json=json.dumps(dTemplate, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    # create the configuration file
    try:
        f_tmpl = open(amc.dRTK['options']['template'])
        glab_templ = Template(f_tmpl.read())

        # substitute the variables in the template file
        glab_cfg = glab_templ.substitute(dTemplate)

        # save to configuration file
        fd_cfg = open(os.path.join(amc.dRTK['proc']['dir_glab'], amc.dRTK['proc']['glab_cfg']), 'w')
        fd_cfg.write(glab_cfg)
        fd_cfg.close()

        logger.info('{func:s}: created glab configuration file {cfg:s}\n{content!s}'.format(cfg=amc.dRTK['proc']['glab_cfg'], content=glab_cfg, func=cFuncName))

    except IOError:
        logger.info('{func:s}: problems using template file {tmpl:s}'.format(tmpl=amc.dRTK['options']['template'], func=cFuncName))
        sys.exit(amc.E_FILE_NOT_EXIST)


def run_glabng_session(logger: logging.Logger):
    """
    run_glabng_session runs gLAB (v6.x) using provided configuration file
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # uncompress the RINEX OBS file
    runGLABNG = '{prog:s} -input:cfg {cfg:s}'.format(prog=amc.dRTK['progs']['glabng'], cfg=os.path.join(amc.dRTK['proc']['dir_glab'], amc.dRTK['proc']['glab_cfg']))
    logger.info('{func:s}: Running:\n{cmd:s}'.format(func=cFuncName, cmd=colored(runGLABNG, 'green')))

    # run the program
    exeprogram.subProcessDisplayStdOut(cmd=runGLABNG, verbose=True)

    # compress the resulting "out" file
    runGZIP = '{prog:s} -f {zip:s}'.format(prog=amc.dRTK['progs']['gzip'], zip=os.path.join(amc.dRTK['proc']['dir_glab'], amc.dRTK['proc']['glab_out']))
    logger.info('{func:s}: compressing {out:s} file by:\n{cmd:s}'.format(out=amc.dRTK['proc']['glab_out'], func=cFuncName, cmd=colored(runGZIP, 'green')))
    # run the program
    exeprogram.subProcessDisplayStdErr(cmd=runGZIP, verbose=True)

    runGZIP


def main(argv) -> bool:
    """
    glabplotposn plots data from gLAB (v6) OUTPUT messages

    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # store cli parameters
    amc.dRTK = {}
    cli_opt = {}
    cli_opt['rxtype'], cli_opt['igs_root'], cli_opt['marker'], cli_opt['year'], cli_opt['doy'], cli_opt['gnss'], cli_opt['prcodes'], cli_opt['cutoff'], cli_opt['template'], log_levels = treatCmdOpts(argv)
    amc.dRTK['options'] = cli_opt

    # check some arguments

    # create logging for better debugging
    logger, log_name = amc.createLoggers(os.path.basename(__file__), dir=os.getcwd(), logLevels=log_levels)

    ret_val = check_arguments(logger=logger)
    if ret_val != amc.E_SUCCESS:
        sys.exit(ret_val)

    # locate the program used for execution
    amc.dRTK['progs'] = {}
    amc.dRTK['progs']['glabng'] = location.locateProg('glabng', logger)
    amc.dRTK['progs']['crz2rnx'] = location.locateProg('crz2rnx', logger)
    amc.dRTK['progs']['gunzip'] = location.locateProg('gunzip', logger)
    amc.dRTK['progs']['gzip'] = location.locateProg('gzip', logger)

    # uncompress RINEX files
    uncompress_rnx_files(logger=logger)

    # use the template file for creation of glab config file
    create_session_template(logger=logger)

    # run glabng using created cfg file
    run_glabng_session(logger=logger)

    # remove the decompressed RINEX files
    cleanup_rnx_files(logger=logger)

    # report to the user
    logger.info('{func:s}: Project information =\n{json!s}'.format(func=cFuncName, json=json.dumps(amc.dRTK, sort_keys=False, indent=4, default=amutils.DT_convertor)))

    # move the log file to the glab directory
    code_txt = ''
    for code in amc.dRTK['proc']['codes']:
        code_txt += ('_' + code)
    move(log_name, os.path.join(amc.dRTK['proc']['dir_glab'], 'glab_proc_{gnss:s}{prcodes:s}.log'.format(gnss=''.join(amc.dRTK['proc']['gnss']), prcodes=code_txt)))

    return amc.E_SUCCESS


if __name__ == "__main__":  # Only run if this file is called directly
    main(sys.argv)
