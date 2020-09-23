#!/usr/bin/env python

# location searchs in PATH for existence of program
import sys                      # import module sysimport os
from sys import platform
import os                       # getting to the OS
from termcolor import colored
import logging
import am_config as amc


def whereis(progName, logger: logging.Logger = None):
    """
    Search whether a progName is in the $PATH

    :param progName: progName to serach for in the $PATH
    :type progName: string

    :returns: if progName found, returns the full path to it else None returned
    :rtype: string
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    if platform == "win32":
        filename, file_extension = os.path.splitext(progName)
        if file_extension != '.exe' or file_extension != '.com':
            progName = progName + '.exe'

    for path in os.environ.get('PATH', '').split(os.pathsep):
        exeProgram = os.path.join(path, progName)
        if os.path.exists(exeProgram) and not os.path.isdir(exeProgram) and os.access(exeProgram, os.X_OK):
            return exeProgram

    # not found, so display this
    user_paths = os.environ['PATH'].split(os.pathsep)
    if logger is not None:
        logger.info('{func:s} !!! progName {prog:s} not found in PATH {path!s}'.format(func=cFuncName, prog=progName, path=user_paths))
    else:
        sys.stderr.write('progName %s not found in PATH %s\n' % (colored(progName, 'red'), user_paths))

    return None


def locateProg(progName, logger: logging.Logger = None):
    """
    locateProg locates porgName in $PATH

    :param progName: progName to serach for in the $PATH
    :type progName: string

    :returns exeProg: programs with full path
    :rtype exeProg: string
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # logger.info('{func:s}: locate programs {prog:s}'.format(func=cFuncName, prog=progName))

    exePROG = whereis(progName, logger)
    if exePROG is None:
        if logger is not None:
            logger.info('{func:s} !!! did not found executable {prog:s} in path. Program Exits\n'.format(func=cFuncName, prog=progName))
        else:
            sys.stderr.write(colored(('!!! did not found executable %s in path. Program Exits\n' % progName), 'red'))
        sys.exit(amc.E_NOT_IN_PATH)

    logger.info('{func:s}: {prog:s} is {cmd:s}'.format(func=cFuncName, prog=progName, cmd=colored(exePROG, 'green')))

    return exePROG


def main(argv):
    """
    main function starts here (only for testing), call like ``location.py sbf2rin``
    """
    location = whereis(argv[1])
    if location is not None:
        print(location)
        sys.exit(amc.E_SUCCESS)
    else:
        sys.exit(amc.E_NOT_IN_PATH)

# main starts here
if __name__ == '__main__':
    main(sys.argv)
