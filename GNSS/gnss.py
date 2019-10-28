#!/usr/bin/env python


"""
Container for general GNSS related classes
Classes:
    GNSS
"""
# Import required packages
from GNSS import wgs84


class GNSS:
    """
    Working class for GNSS module

    Determines the constants used by GNSS systems
    """

    wgs84 = wgs84.WGS84()

    # Constants for GNSS
    f0 = 10230E3

    fGPS_L1 = f0 * 154.0
    fGPS_L2 = f0 * 120.0
    fGPS_L5 = f0 * 115.0

    fGAL_E1A = fGPS_L1
    fGAL_E1BC = fGPS_L1
    fGAL_E6A = f0 * 125.0
    fGAL_E6BC = fGAL_E6A
    fGAL_E5A = fGPS_L5
    fGAL_E5B = f0 * 118.0
    fGAL_E5 = f0 * 116.5
    fGEO_L1 = f0 * 154.0
    fGEO_L5 = f0 * 115.0
    fQZSS_L5 = f0 * 115.0
    fCMP_L1 = f0 * 152.6
    fCMP_E5b = f0 * 118
    Res = 0

    l1 = wgs84.c / fGPS_L1
    l2 = wgs84.c / fGPS_L2
    l5 = wgs84.c / fGPS_L5
