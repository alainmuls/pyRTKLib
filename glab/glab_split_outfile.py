from termcolor import colored
import sys
import os
import logging
import tempfile

__author__ = 'amuls'


def split_glab_outfile(msgs: str, glab_outfile: str, logger: logging.Logger) -> dict:
    """
    splitStatusFile splits the statistics file into the POS, SAT, CLK & VELACC parts
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: splitting gLABs out file {statf:s} ({info:s})'.format(func=cFuncName, statf=colored(glab_outfile, 'yellow'), info=colored('be patient', 'red')))

    # create the temporary files needed for this parsing
    dtmp_fnames = {}
    dtmp_fds = {}
    for glab_msg in msgs:
        dtmp_fnames[glab_msg] = tempfile.NamedTemporaryFile(prefix='{:s}_'.format(glab_outfile), suffix='_{:s}'.format(glab_msg), delete=True)
        dtmp_fds[glab_msg] = open(dtmp_fnames[glab_msg].name, 'w')

    # open gLABng '*.out' file for reading and start processing its lines parsing the selected messages
    with open(glab_outfile, 'r') as fd:
        line = fd.readline()
        while line:
            for glab_msg in msgs:
                if line.startswith(glab_msg):
                    dtmp_fds[glab_msg].write(line)
            line = fd.readline()

    # close the opened files
    for glab_msg in msgs:
        dtmp_fds[glab_msg].close()

        # return the dict with the temporary filenames created
    return dtmp_fnames
