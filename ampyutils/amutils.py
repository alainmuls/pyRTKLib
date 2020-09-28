from __future__ import print_function

import sys
import errno
import os
from termcolor import colored
import webcolors
import gzip
import shutil
import logging
from pandas import DataFrame
import subprocess
from datetime import datetime
from typing import Tuple
import matplotlib._color_data as mcd
import enum
import numpy as np
import pandas as pd
from tabulate import tabulate

from ampyutils import exeprogram
from GNSS import gpstime
import am_config as amc

__author__ = 'amuls'


# Enum for size units
class SIZE_UNIT(enum.Enum):
    BYTES = 1
    KB = 2
    MB = 3
    GB = 4


def mkdir_p(path):
    """
    python implementation of mkdir -p for bash

    :param path: path to create
    :type path: string
    """
    try:
        # print('path = %s' % path)
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def CheckFile(filename, verbose=False):
    """
    check if a file exists

    :param filename: name of file to check
    :type filename: string
    """
    if not os.path.isfile(filename):
        if verbose:
            sys.stderr.write('File %s does not exists. \n' % filename)
        return False
    else:
        return True


def CheckDir(directory, verbose=False):
    """
    check if a directory exists

    :param directory: name of directory to check
    :type directory: string
    """
    if not os.path.isdir(directory):
        if verbose:
            sys.stderr.write('Directory %s does not exists. \n' % directory)
        return False
    else:
        return True


def changeDir(directory, verbose=False):
    """
    check if directory exists and change to it, else abort

    :param directory: name of directory to check
    :type directory: string
    """
    # change to the directory if it exists
    workDir = os.getcwd()
    # if directory[0] is not '.':
    #    print('in if %s' % workDir)
    workDir = os.path.normpath(os.path.join(workDir, directory))

    # print('workDir = %s' % workDir)
    if not os.path.exists(workDir):
        if verbose:
            sys.stderr.write('Directory %s does not exists.\n' % workDir)
        return False
    else:
        os.chdir(workDir)
        return True


def changeDirCheckFile(directory, filename, verbose=False):
    """
    changeDirCheckFile checks whether the directory and file exist

    :param directory: name of directory to check
    :type directory: string
    :param filename: name of file to check
    :type filename: string
    :returns: True or False
    """
    if changeDir(directory, verbose):
        return CheckFile(filename, verbose)
    else:
        return False


def get_filebasename(path):
    """
    Gets a files basename (without extension) from a provided path
    """
    filename = path.split(os.pathsep)[-1].split(os.extsep)[0]
    return filename


def printHeadTailDataFrame(df: pd.DataFrame, name: str, index: str = True, head: int = 10, tail: int = 10):
    """
    printHeadTailDataFrame prints the head first/tail last rows of the dataframe df

    :param df: dataframe to print
    :type df: dataframe
    :param name: name for dataframe (def ``DataFrame``)
    :type name: string
    :param head: nr of lies from start of df
    :type head: int
    :param tail: nr of lies from start of df
    :type tail: int
    :param index: display the index of the dataframe or not
    :type: bool
    """
    if df.shape[0] <= (head + tail):
        print('\n   ...  %s (size %d)\n%s' % (colored(name, 'green'), df.shape[0], df.to_string(index=index)))
    else:
        print('\n   ... Head of %s (size %d)' % (colored(name, 'green'), df.shape[0]))
        print(df.head(n=head).to_string(index=index))
        print('   ... Tail of %s (size %d)\n%s' % (colored(name, 'green'), df.shape[0], df.tail(n=tail).to_string(index=index)))


def pprint_df(dframe: pd.DataFrame, tablefmt: str = 'simple'):
    print(tabulate(dframe, headers='keys', tablefmt=tablefmt, showindex=False))


def logHeadTailDataFrame(logger: logging.Logger, callerName: str, df: DataFrame, dfName: str = 'DataFrame', head: int = 10, tail: int = 10, index: bool = True):
    """
    logHeadTailDataFrame logs the head first/tail last rows of the dataframe df

    :param df: dataframe to log
    :type df: dataframe
    :param name: name for dataframe (def ``DataFrame``)
    :type name: string
    :param head: nr of lies from start of df
    :type head: int
    :param tail: nr of lies from start of df
    :type tail: int
    :param index: display th eindex of the dataframe or not
    :type: bool
    """
    # cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    print('{func:s}: dataframe {dfname:s} dtypes\n{dtypes!s}'.format(dtypes=df.dtypes, dfname=colored(dfName, 'green'), func=callerName))

    if df.shape[0] <= (head + tail):
        logger.info('{func:s}: dataframe {dfname:s} (#{shape:d})\n{df:s}'.format(func=callerName, dfname=colored(dfName, 'green'), shape=df.shape[0], df=df.to_string(index=index)))
    else:
        logger.info('{func:s}: head of dataframe {dfname:s} (#{shape:d})\n{df:s}'.format(func=callerName, dfname=colored(dfName, 'green'), shape=df.shape[0], df=df.head(n=head).to_string(index=index)))
        logger.info('{func:s}: tail of dataframe {dfname:s} (#{shape:d})\n{df:s}'.format(func=callerName, dfname=colored(dfName, 'green'), shape=df.shape[0], df=df.tail(n=tail).to_string(index=index)))


def get_spaced_colors(n):
    """
    getSpacedColors gets the colors spaced in the list of cnames

    :param n: number of colors to cylce through
    :type n: int
    :returns color: list of minimum size n
    :rtype color: list
    """
    max_value = 16581375  # 255**3
    interval = int(max_value / n)
    colors = [hex(I)[2:].zfill(6) for I in range(0, max_value, interval)]

    return [(int(i[:2], 16), int(i[2:4], 16), int(i[4:], 16)) for i in colors]


def closest_colour(requested_colour):
    """
    closest_colour searches in color space for the closest named color. It matches by Euclidian distance in the RGB space.

    :param requested_colour: RGB representation of a color
    :int requested_colour: tuple
    :returns min_colours: closest normalised color
    :rtype min_colours: tuple
    """
    min_colours = {}
    for key, name in webcolors.css3_hex_to_names.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_colour_name(requested_colour):
    """
    get_colour_name gets the normalised name of the colour or its closest neigbour in RGB space with a normalised name

    :param requested_colour: RGB representation of a color
    :int requested_colour: tuple
    :returns actual_name: normalised name of actual color
    :rtype actual_name: string
    :returns closest_name: normalised name of closest color
    :rtype closest_name: string
    """
    try:
        closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
        actual_name = None
    return actual_name, closest_name


def dump(obj, nested_level=0, output=sys.stdout):
    """
    dumps a dictionary or list to the output

    :param obj: object to dump
    :type obj: dictionary or list
    :param nested_level: how depp to nest the levels of the object
    :type nested_level: int
    :param output: where to write output to
    :type output: filedescriptor
    """
    spacing = '   '
    if type(obj) == dict:
        print(('%s{' % ((nested_level) * spacing)), file=output)
        for k, v in obj.items():
            if hasattr(v, '__iter__') and type(v) is not str:
                print('%s%s:' % ((nested_level + 1) * spacing, k), file=output)
                dump(v, nested_level + 1, output)
            else:
                print('%s%s: %s' % ((nested_level + 1) * spacing, k, v), file=output)
        print(('%s}' % (nested_level * spacing)), file=output)
    elif type(obj) == list:
        print(('%s[' % ((nested_level) * spacing)), file=output)
        for v in obj:
            if hasattr(v, '__iter__'):
                dump(v, nested_level + 1, file=output)
            else:
                print('%s%s' % ((nested_level + 1) * spacing, v), file=output)
        print(('%s]' % ((nested_level) * spacing)), file=output)
    else:
        print(('%s%s' % (nested_level * spacing, obj)), file=output)


def line_num_for_phrase_in_file(phrase='the dog barked', filename='file.txt'):
    """
    line_num_for_phrase_in_file gets the line number for a sentence in a file

    :param phrase: phrase to search for
    :type phrase: string
    :param filename: name of file to search in
    :type filename: string
    :returns: linenumber of searched text, if not founf returns -1
    :rtype: int
    """
    with open(filename, 'r') as f:
        for (i, line) in enumerate(f):
            if phrase in line:
                return i
    return -1


def hms2sec(x):
    """
    hms2sec converts a string in HH:MM:SS.SS into a float value

    :param x: time expressed as HH:MM:SS.SS
    :type x: string
    :returns: number of seconds
    :rtype: float
    """
    times = x.split(':')
    return (60 * float(times[0]) + float(times[1])) * 60 + float(times[2])


def tow2sod(x):
    """
    tow2sec converts a string in TOW into a float value

    :param x: time expressed as TOW
    :type x: string
    :returns: number of seconds
    :rtype: float
    """
    return(x % gpstime.SECSINDAY)


def count_lines(filename):
    f = open(filename)
    lines = 0
    buf_size = 1024 * 1024
    read_f = f.read  # loop optimization

    buf = read_f(buf_size)
    while buf:
        lines += buf.count('\n')
        buf = read_f(buf_size)

    # print('lines = {}'.format(lines))
    return lines


def decompress(fileCompName: str, fileName: str):
    """
    decompresses fileCompName
    """
    with open(fileName, 'wb') as f_out, gzip.open(fileCompName, 'rb') as f_in:
        shutil.copyfileobj(f_in, f_out)


def make_rgb_transparent(rgb, bg_rgb, alpha):
    """
    make a color transparent
    """
    return [alpha * c1 + (1 - alpha) * c2
            for (c1, c2) in zip(rgb, bg_rgb)]


def run_subprocess(sub_proc: list, logger: logging.Logger):
    """
    run_subprocess runs the program with arguments in the sub_proc list
    """
    cFuncName = colored(os.path.basename(__file__), 'yellow') + ' - ' + colored(sys._getframe().f_code.co_name, 'green')

    # convert all arguments to str
    strargs = [str(arg) for arg in sub_proc if arg is not str]
    # print(' '.join(strargs))

    try:
        logger.info('{func:s}: running\n{proc:s}'.format(proc=colored(' '.join(strargs), 'blue'), func=cFuncName))
        subprocess.check_call(strargs, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        # handle errors in the called executable
        logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=strargs[0], err=e))
        sys.exit(amc.E_SBF2RIN_ERRCODE)
    except OSError as e:
        # executable not found
        logger.error('{func:s}: subprocess {proc:s} returned error code {err!s}'.format(func=cFuncName, proc=strargs[0], err=e))
        sys.exit(amc.E_OSERROR)


def DT_convertor(o):
    if isinstance(o, datetime):
        return o.__str__()


def create_colormap_font(nrcolors: int, font_size: int) -> Tuple[list, dict]:
    """
    create_colormap_font creates a colormap for the number entered and returns a color list and dict with fonts for title and axes
    """
    # get the color names
    color_names = [name for name in mcd.XKCD_COLORS]
    color_step = len(color_names) // nrcolors
    color_used = color_names[::color_step]

    font = {'family': 'serif',
            # 'color': 'darkred',
            'weight': 'bold',
            'size': font_size,
            }

    return color_used, font


def convert_unit(size_in_bytes, unit):
    """ Convert the size from bytes to other units like KB, MB or GB"""
    if unit == SIZE_UNIT.KB:
        return size_in_bytes / 1024
    elif unit == SIZE_UNIT.MB:
        return size_in_bytes / (1024 * 1024)
    elif unit == SIZE_UNIT.GB:
        return size_in_bytes / (1024 * 1024 * 1024)
    else:
        return size_in_bytes


def wavg(group: dict, avg_name: str, weight_name: str) -> float:
    """ http://stackoverflow.com/questions/10951341/pandas-dataframe-aggregate-function-using-multiple-columns
    In rare instance, we may not have weights, so just return the mean. Customize this if your business case
    should return otherwise.
    """
    coordinate = group[avg_name]
    invVariance = 1 / np.square(group[weight_name])

    try:
        return (coordinate * invVariance).sum() / invVariance.sum()
    except ZeroDivisionError:
        return coordinate.mean()


def stddev(crd: pd.Series, avgCrd: float) -> float:
    """
    stddev calculates the standard deviation of series
    """
    dCrd = crd.subtract(avgCrd)

    return dCrd.std()
