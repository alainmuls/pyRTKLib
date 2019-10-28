import datetime
from termcolor import colored
import argparse




def valid_date_type(arg_date_str):
    """
    custom argparse *date* type for user dates values given from the command line
    """
    try:
        # print('arg_date_str = {!s}'.format(arg_date_str))
        return datetime.datetime.strptime(arg_date_str, "%Y-%m-%d")
    except ValueError:
        msg = "Given Date ({0}) not valid! Expected format, 'YYYY-MM-DD'!".format(colored(arg_date_str, 'red'))
        raise argparse.ArgumentTypeError(msg)


def valid_datetime_type(arg_datetime_str):
    """
    custom argparse type for user datetime values given from the command line
    """
    try:
        # print('arg_datetime_str = {!s}'.format(arg_datetime_str))
        return datetime.datetime.strptime(arg_datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        msg = "Given Datetime ({0}) not valid! Expected format, 'YYYY-MM-DD hh:mm'!".format(colored(arg_datetime_str, 'red'))
        raise argparse.ArgumentTypeError(msg)


def valid_timeHM_type(arg_time_str):
    """
    custom argparse type for user time values given from the command line
    """
    try:
        # print('arg_timeHM_str = {!s}'.format(arg_time_str))
        return datetime.datetime.strptime(arg_time_str, "%H:%M").time()
    except ValueError:
        msg = "Given time ({0}) not valid! Expected format, 'hh:mm'!".format(colored(arg_time_str, 'red'))
        raise argparse.ArgumentTypeError(msg)


def valid_timeHMS_type(arg_time_str):
    """
    custom argparse type for user time values given from the command line
    """
    try:
        # print('arg_timeHMS_str = {!s}'.format(arg_time_str))
        return datetime.datetime.strptime(arg_time_str, "%H:%M:%S").time()
    except ValueError:
        msg = "Given time ({0}) not valid! Expected format, 'hh:mm:ss'!".format(colored(arg_time_str, 'red'))
        raise argparse.ArgumentTypeError(msg)


def valid_interval_type(arg_interval_str):
    """
    custom argparse type for user time intervals given from the command line
    """
    try:
        # print('arg_interval_str = {!s}'.format(arg_interval_str))
        # split according to '-' sign
        times = [hms for hms in arg_interval_str.split('-')]
        intervalTimes = [datetime.datetime.strptime(time, '%H:%M:%S').time() for time in times]
        for time in times:
            # print('times found {!s}'.format(time))
        # print('intervalTimes {!s}'.format(intervalTimes))
        return intervalTimes
    except ValueError:
        msg = "Given time interval ({0}) not valid! Expected format, 'hh:mm:ss-hh:mm:ss'!".format(colored(arg_interval_str, 'red'))
        raise argparse.ArgumentTypeError(msg)


def moving_integer(x):
    val = int(x)
    if val < 5:
        raise argparse.ArgumentTypeError("Minimum number of samples for moving average is 5")
    return val
