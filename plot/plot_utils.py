import time
import sys
import os
from collections import OrderedDict
import numpy as np
from termcolor import colored
import datetime

from GNSS import gpstime
from ampyutils import amutils

__author__ = 'amuls'


def determineTimeTicks(firstObs, lastObs):
    """
    determineTimeTicks sets the min, max and ticks on the time axis based on input in TOWs and reduces to the time of day in seconds

    :param firstObs: first Observation TOW in seconds
    :type firstObs: int
    :param lastObs: last observation TOW in seconds
    :type firstObs: int
    :returns: minSeconds, maxSeconds, listSeconds which are times of day in [0..86400]
    :rtype: int, int, list of int
    """
    # set and clarify the the xticks time labels
    minSeconds = int(firstObs / gpstime.SECSINDAY) * gpstime.SECSINDAY
    maxSeconds = (int(lastObs / gpstime.SECSINDAY) + 1) * gpstime.SECSINDAY
    # print('Seconds = %f - %f - %f' % (minSeconds, maxSeconds, gpstime.SECSINHOUR))
    rangeHours = int(round((maxSeconds - minSeconds) / gpstime.SECSINHOUR))  # number of hours
    # print('Seconds = %f - %f - %f' % (minTOW, maxTOW, rangeTOW))

    if rangeHours < 3:
        rangeHours = rangeHours * 4 + 1
        intervalSeconds = gpstime.SECSINQUARTER
    elif rangeHours < 5:
        rangeHours = rangeHours * 2 + 1
        intervalSeconds = gpstime.SECSINHALFHOUR
    elif rangeHours < 7:
        rangeHours = rangeHours + 1
        intervalSeconds = gpstime.SECSINHOUR
    else:
        rangeHours = int(round(rangeHours / 2)) + 1
        intervalSeconds = gpstime.SECSINTWOHOUR

    # print('Seconds = %f - %f - %f - %f' % (minSeconds, maxSeconds, rangeHours, intervalSeconds))
    listSeconds = [minSeconds + i * intervalSeconds for i in range(0, rangeHours)]
    # print('listSeconds = %s' % listSeconds)

    return minSeconds, maxSeconds, listSeconds


def determine_datetime_ticks(startDT: datetime.datetime, endDT: datetime.datetime) -> dict:
    """
    determines interval and format of minor and major ticks for the time axis
    """
    rangeSeconds = (endDT - startDT + datetime.timedelta(seconds=1)).total_seconds()
    rangeHours = divmod(rangeSeconds, gpstime.SECSINHOUR)[0]

    dTimeFormatter = {}
    # dTimeFormatter['minutes'] = False
    # dTimeFormatter['hourInterval'] = 3

    if rangeHours < 7:
        dTimeFormatter['minutes'] = True
        dTimeFormatter['hourInterval'] = 1
    else:
        dTimeFormatter['minutes'] = False
        dTimeFormatter['hourInterval'] = 3

    # print('dTimeFormatter = {!s}'.format(dTimeFormatter))

    return dTimeFormatter
