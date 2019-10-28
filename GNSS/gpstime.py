#!/usr/bin/env python

"""
A Python implementation of GPS related time conversions.

Copyright 2002 by Bud P. Bruegger, Sistema, Italy
mailto:bud@sistema.it
http://www.sistema.it

Modifications for GPS seconds by Duncan Brown

PyUTCFromGpsSeconds added by Ben Johnson

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation; either version 2 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License along
with this program; if not, write to the Free Software Foundation, Inc., 59
Temple Place, Suite 330, Boston, MA  02111-1307  USA

GPS Time Utility functions

This file contains a Python implementation of GPS related time conversions.

The two main functions convert between UTC and GPS time (GPS-week, time of
week in seconds, GPS-day, time of day in seconds).  The other functions are
convenience wrappers around these base functions.

A good reference for GPS time issues is:
http://www.oc.nps.navy.mil/~jclynch/timsys.html

Note that python time types are represented in seconds since (a platform
dependent Python) Epoch.  This makes implementation quite straight forward
as compared to some algorigthms found in the literature and on the web.
"""

# __author__ = 'Duncan Brown <duncan@gravity.phys.uwm.edu>'
# from glue import git_version
# __date__ = git_version.date
# __version__ = git_version.id

import time
import datetime
import math
import numpy as np

SECSINWEEK = 604800
SECSINDAY = 86400
SECSINHOUR = 3600
SECSINHALFHOUR = 1800
SECSINQUARTER = 900
SECSINTWOHOUR = 7200
SECSINTHREEHOUR = 10800
DT06JAN80 = (1980, 1, 6, 0, 0, 0)  # (year, month, day, hh, mm, ss)


def dayOfWeek(year, month, day):
    """
    returns the day of week starting on Sunday=0

    :param year: the year
    :type year: int
    :param month: the month
    :type month: int
    :param day: the day
    :type day: int
    :returns: day of week: 0=Sun, 1=Mon, .., 6=Sat
    :rtype: int
    """
    hr = 12  # make sure you fall into right day, middle is save
    t = time.mktime((year, month, day, hr, 0, 0, 0, 0, -1))
    pyDow = time.localtime(t)[6]
    gpsDow = (pyDow + 1) % 7

    return gpsDow


def gpsWeek(year, month, day):
    """
    returns (full) gpsWeek for given date (in UTC)

    :param year: the year
    :type year: int
    :param month: the month
    :type month: int
    :param day: the day
    :type day: int
    :returns: full GPS week
    :rtype: int
    """
    hr = 12  # make sure you fall into right day, middle is save
    return gpsFromUTC(year, month, day, hr, 0, 0.0)[0]


def julianDay(year, month, day):
    """
    returns julian day=day since Jan 1 of year

    :param year: the year
    :type year: int
    :param month: the month
    :type month: int
    :param day: the day
    :type day: int
    :returns: julian day
    :rtype: float
    """
    hr = 12  # make sure you fall into right day, middle is save
    # print('\n\nyear %s = %s' % (type(year), year))
    # print('month %s = %s' % (type(month), month))
    # print('day %s = %s' % (type(day), day))

    t = time.mktime((year, month, day, hr, 0, 0, 0, 0, -1))
    julDay = time.localtime(t)[7]

    return julDay


def mkUTC(year, month, day, hour, min, sec):
    """
    similar to python's mktime but for utc

    :param year: the year
    :type year: int
    :param month: the month
    :type month: int
    :param day: the day
    :type day: int
    :param hour: the hour
    :type hour: int
    :param min: the minutes
    :type min: int
    :param sec: the seconds
    :type sec: float
    :returns: UTC time
    :rtype: time structure
    """
    if float(sec).is_integer():
        msec = 0
    else:
        msec = float(str(sec-int(sec))[1:])
    spec = [year, month, day, hour, min, int(math.floor(sec))] + [0, 0, 0]
    # print('\n\nyear %s = %s' % (type(year), year))
    # print('month %s = %s' % (type(month), month))
    # print('day %s = %s' % (type(day), day))
    # print('hour %s = %s' % (type(hour), hour))
    # print('min %s = %s' % (type(min), min))
    # print('sec %s = %s' % (type(sec), sec))
    # print('spec %s' % spec)
    utc = time.mktime(spec) + msec - time.timezone
    return utc


def ymdhmsFromPyUTC(pyUTC):
    """
    returns tuple from a python time value in UTC

    :param pyUTC: UTC time
    :type pyUTC: timestamp
    :returns: date and time that corresponds to pyUTC
    :rtype: datetime
    """
    # print("PYUTC", pyUTC)
    # ymdhmsXXX = time.gmtime(pyUTC)
    # return ymdhmsXXX[:-3]
    return datetime.datetime.utcfromtimestamp(pyUTC)


def wtFromUTCpy(pyUTC, leapSecs=14):
    """
    convenience function:
         allows to use python UTC times and
         returns only week and tow
    """
    ymdhms = ymdhmsFromPyUTC(pyUTC)
    wSowDSoD = apply(gpsFromUTC, ymdhms.timetuple()[:6] + (leapSecs,))
    return wSowDSoD[0:2]


def gpsFromUTC(year, month, day, hour, min, sec, leapSecs=14):
    """converts UTC to: gpsWeek, secsOfWeek, gpsDay, secsOfDay

    a good reference is:  http://www.oc.nps.navy.mil/~jclynch/timsys.html

    This is based on the following facts (see reference above):

    GPS time is basically measured in (atomic) seconds since
    January 6, 1980, 00:00:00.0  (the GPS Epoch)

    The GPS week starts on Saturday midnight (Sunday morning), and runs
    for 604800 seconds.

    Currently, GPS time is 14 seconds ahead of UTC (see above reference).
    While GPS SVs transmit this difference and the date when another leap
    second takes effect, the use of leap seconds cannot be predicted.  This
    routine is precise until the next leap second is introduced and has to be
    updated after that.

    SOW = Seconds of Week
    SOD = Seconds of Day

    Note:  Python represents time in integer seconds, fractions are lost!!!
    """
    # secFract = sec
    # secFract = sec % 1
    epochTuple = DT06JAN80 + (-1, -1, 0)
    t0 = time.mktime(epochTuple)
    # print('\n\nyear %s = %s' % (type(year), year))
    # print('month %s = %s' % (type(month), month))
    # print('day %s = %s' % (type(day), day))
    # print('hour %s = %s' % (type(hour), hour))
    # print('min %s = %s' % (type(min), min))
    # print('sec %s = %s' % (type(sec), sec))
    if float(sec).is_integer():
        msec = 0
    else:
        msec = float(str(sec-int(sec))[1:])

    t = time.mktime((year, month, day, hour, min, int(sec), -1, -1, 0))
    # Note: time.mktime strictly works in localtime and to yield UTC, it should be
    #       corrected with time.timezone
    #       However, since we use the difference, this correction is unnecessary.
    # Warning:  trouble if daylight savings flag is set to -1 or 1 !!!
    t = t + leapSecs
    tdiff = t - t0
    gpsSOW = (tdiff % SECSINWEEK) + msec
    # gpsSOW = (tdiff % SECSINWEEK) + secFract
    gpsWeek = int(math.floor(tdiff/SECSINWEEK))
    gpsDay = int(math.floor(gpsSOW/SECSINDAY))
    gpsSOD = (gpsSOW % SECSINDAY)
    return (gpsWeek, gpsSOW, gpsDay, gpsSOD)


def UTCFromGps(gpsWeek, SOW, leapSecs=14):
    """converts gps week and seconds to UTC

    see comments of inverse function!

    SOW = seconds of week
    gpsWeek is the full number (not modulo 1024)
    """
    secFract = SOW % 1
    epochTuple = DT06JAN80 + (-1, -1, 0)
    t0 = time.mktime(epochTuple) - time.timezone  # mktime is localtime, correct for UTC
    tdiff = (gpsWeek * SECSINWEEK) + SOW - leapSecs
    t = t0 + tdiff
    (year, month, day, hh, mm, ss, dayOfWeek, julianDay, daylightsaving) = time.gmtime(t)
    # use gmtime since localtime does not allow to switch off daylighsavings correction!!!
    return (year, month, day, hh, mm, ss + secFract)


def UTCFromString(year, month, day, dataString):
    """
    converts string into UTC date time dataString=hh:mm:ss
    """
    hh = int(dataString[0:2])
    mm = int(dataString[3:5])
    ss = int(dataString[6:8])
    time = datetime.datetime(year, month, day, hh, mm, ss)

    return time


def GpsSecondsFromPyUTC(pyUTC, leapSecs=14):
    """converts the python epoch to gps seconds

    pyEpoch = the python epoch from time.time()
    """
    t = gpsFromUTC(*ymdhmsFromPyUTC(pyUTC))
    return int(t[0] * 60 * 60 * 24 * 7 + t[1])


def DOWFromWT(tow):
    """get DOW from Weektime"""
    DAYOW = np.floor(tow / (60*60*24))
    return int(DAYOW)


def UTCFromWT(weeknr, tow):
    """
    get UTC time from weektime
    """
    datum = datetime.datetime(1980, 1, 6, 0, 0, 0)
    week = datetime.timedelta(weeks=weeknr)
    sec = datetime.timedelta(seconds=tow)
    time = datum+week+sec
    return time

# def PyUTCFromGpsSeconds(gpsseconds):
#     """converts gps seconds to the
#     python epoch. That is, the time
#     that would be returned from time.time()
#     at gpsseconds.
#     """
#     pyUTC

# ===== Tests  =========================================


def testTimeStuff():
    """test the time stuff"""
    print("-" * 20)
    print("The GPS Epoch when everything began (1980, 1, 6, 0, 0, 0, leapSecs=0)")
    (w, sow, d, sod) = gpsFromUTC(1980, 1, 6, 0, 0, 0, leapSecs=0)
    print("**** week: %s, sow: %s, day: %s, sod: %s" % (w, sow, d, sod))
    print("     and hopefully back:")
    print("**** %s, %s, %s, %s, %s, %s\n" % UTCFromGps(w, sow, leapSecs=0))

    print("The time of first Rollover of GPS week (1999, 8, 21, 23, 59, 47)")
    (w, sow, d, sod) = gpsFromUTC(1999, 8, 21, 23, 59, 47)
    print("**** week: %s, sow: %s, day: %s, sod: %s" % (w, sow, d, sod))
    print("     and hopefully back:")
    print("**** %s, %s, %s, %s, %s, %s\n" % UTCFromGps(w, sow, leapSecs=14))

    print("Today is GPS week 1186, day 3, seems to run ok (2002, 10, 2, 12, 6, 13.56)")
    (w, sow, d, sod) = gpsFromUTC(2002, 10, 2, 12, 6, 13.56)
    print("**** week: %s, sow: %s, day: %s, sod: %s" % (w, sow, d, sod))
    print("     and hopefully back:")
    print("**** %s, %s, %s, %s, %s, %s\n" % UTCFromGps(w, sow))


def testJulD():
    """test julian date"""
    print('2002, 10, 11 -> 284  ==??== ', julianDay(2002, 10, 11))


def testGpsWeek():
    """test gps week"""
    print('2002, 10, 11 -> 1187  ==??== ', gpsWeek(2002, 10, 11))


def testDayOfWeek():
    """test day of week"""
    print('2002, 10, 12 -> 6  ==??== ', dayOfWeek(2002, 10, 12))
    print('2002, 10, 6  -> 0  ==??== ', dayOfWeek(2002, 10, 6))


def testPyUtilties():
    """test utilities"""
    ymdhms = (2002, 10, 12, 8, 34, 12.3)
    print("testing for: ", ymdhms)

    pyUtc = apply(mkUTC, ymdhms)
    back = ymdhmsFromPyUTC(pyUtc)
    print("yields     : ", back)
# *********************** !!!!!!!!
    # assert(ymdhms == back)
    # ! TODO: this works only with int seconds!!! fix!!!

    # FIXED: Use of DATETIME (resolution of 1 microsec) in stead of TIME (resolution 1 sec)
    (w, t) = wtFromUTCpy(pyUtc)
    print("week and time: ", (w, t))


# ===== Main =========================================
if __name__ == "__main__":
    pass
    testTimeStuff()
    testGpsWeek()
    testJulD()
    testDayOfWeek()
    testPyUtilties()
