import sys
import os
from termcolor import colored
import logging
from tempfile import mkstemp
from shutil import move, copymode

__author__ = 'amuls'


def open_database(db_name: str, logger: logging.Logger):
    """
    open_database opens (or creates the database file for storing the statistics on daily basis
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Creating / Opening database file {file:s}'.format(func=cFuncName, file=colored(db_name, 'green')))

    if not os.path.exists(db_name):
        open(db_name, 'w').close()


def db_update_line(db_name: str, line_id: str, info_line: str, logger: logging.Logger):
    """
    db_update_line updates a line in the database, when the line exists it will be replaced, else it will be added
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Updating database file {file:s}'.format(func=cFuncName, file=colored(db_name, 'green')))

    # update is set to false, we first search if this line is already existing
    db_updated = False

    # Create temp file
    fd, abs_path = mkstemp()

    with os.fdopen(fd, 'w') as outf:
        with open(db_name, 'r') as inf:
            for line in inf:
                if line.rstrip().startswith(line_id):
                    outf.write(info_line + '\n')
                    db_updated = True
                else:
                    outf.write(line)

        # if update has not happened, than add the line to the database
        if not db_updated:
            # print('adding info_line {:s}'.format(info_line))
            outf.write(info_line + '\n')

    # Copy the file permissions from the old file to the new file
    copymode(db_name, abs_path)

    # Remove original file
    os.remove(db_name)

    # Move new file
    move(abs_path, db_name)


def db_sort(db_name: str, logger: logging.Logger):
    """
    db_sort sorts the database
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    logger.info('{func:s}: Sorting database file {file:s}'.format(func=cFuncName, file=colored(db_name, 'green')))

    # Create temp file
    fd, abs_path = mkstemp()

    # sort database lines
    with open(db_name, 'r') as inf:
        lines = inf.readlines()
    lines.sort()

    with os.fdopen(fd, 'w') as outf:
        outf.writelines(lines)

    # Copy the file permissions from the old file to the new file
    copymode(db_name, abs_path)

    # Remove original file
    os.remove(db_name)

    # Move new file
    move(abs_path, db_name)
