import sys
from termcolor import colored
import subprocess
import time

__author__ = 'amuls'

# exit codes
E_SUCCESS = 0
E_FILE_NOT_EXIST = 1
E_NOT_IN_PATH = 2
E_UNKNOWN_OPTION = 3
E_TIME_PASSED = 4
E_WRONG_OPTION = 5
E_SIGNALTYPE_MISMATCH = 6
E_DIR_NOT_EXIST = 7
E_OSERROR = 10
E_FAILURE = 99


def exeProg(prog, argsProg, verbose=False):
    """
    exeProg executes prog with argsProg

    :param prog: the cmd to execute
    :type prog: string
    :param optProg: the options passed to prog
    :type optProg: array of strings
    """
    try:
        # print('prog: %s, args = %s' % (prog, argsProg))
        runProg = []
        runProg.extend([prog])
        runProg.extend(argsProg)
        # print('runProg = %s  %s' % (runProg, type(runProg)))
        progOutput = subprocess.check_output(runProg, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # handle errors in the called executable
        sys.stderr.write(colored(('%s\n' % e), 'red'))
        sys.exit(E_FAILURE)
    except OSError as e:
        # executable not found
        sys.stderr.write(colored(('%s\n' % e), 'red'))
        sys.exit(E_OSERROR)

    return progOutput


def runProg(prog, optProg, verbose=False):
    """
    Run an external cmd and wait until it finishes (or max time set by TIME2WAIT)

    :param prog: the cmd to execute
    :type prog: string
    :param optProg: the options passed to prog
    :type optProg: array of strings
    :returns: on completion, returns the stdout output of program
    :returns: on error, informs the error and exits
    """
    # some constants used
    TIME2WAIT = 300
    NROFDOTS = 10

    # start the subprocess and use timing to failstop it
    # print('optProg = %s' % optProg)
    progFull = [prog] + optProg
    # print('progFull = %s' % progFull)
    t_nought = time.time()
    p = subprocess.Popen(progFull, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for date to terminate. Get returncode
    seconds_passed = 0
    while(p.poll() is None and seconds_passed < TIME2WAIT):
        # We can do other things here while we wait
        time.sleep(1.)
        seconds_passed = time.time() - t_nought
        if verbose:
            dots = (('.' * (((int)(seconds_passed - 1) % NROFDOTS) + 1)) + (' ' * NROFDOTS))
            sys.stdout.write('  Converting SBF data %s\r' % dots)
            sys.stdout.flush()

    if verbose:
        sys.stdout.write('\n')

    # check the condition at end of execution
    if (seconds_passed >= TIME2WAIT):
        sys.stderr.write('  maximal processing time passed. %s exits.\n' % prog)
        sys.exit(E_TIME_PASSED)
    else:
        (results, errors) = p.communicate()
        # sys.stdout.write("\nCommand output : \n", results)
        # print("error : ", errors)
        if errors == '':
            return results
        else:
            sys.stderr.write("  execution of %s failed with errors %s. %s exits.\n" %
                             (progFull, errors, prog))
            sys.exit(E_FAILURE)


def subProcessDisplayStdErr(cmd, verbose=False):
    """
    subProcessDisplayStdErr runs the cmd and displays in real time the stderr of this process

    :param cmd: contains the program to run with its arguments
    :type cmd: string
    """
    sub_process = subprocess.Popen(cmd, close_fds=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while sub_process.poll() is None:
        out = sub_process.stderr.read(1)
        if verbose:
            sys.stdout.write(out.decode(encoding='UTF-8'))
            sys.stdout.flush()

    if verbose:
        sys.stdout.write('\n')


def subProcessDisplayStdOut(cmd, verbose=False):
    """
    subProcessDisplayStdErr runs the cmd and displays in real time the stderr of this process

    :param cmd: contains the program to run with its arguments
    :type cmd: string
    """
    if verbose:
        print('   Executing cmd: %s' % cmd)

    sub_process = subprocess.Popen(cmd, close_fds=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while sub_process.poll() is None:
        out = sub_process.stdout.read(1)
        if verbose:
            sys.stdout.write(out.decode(encoding='UTF-8'))
            sys.stdout.flush()

    if verbose:
        sys.stdout.write('\n')
