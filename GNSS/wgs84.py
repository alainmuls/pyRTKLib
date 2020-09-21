#!/usr/bin/env python

"""
Container for general Geographic functions and classes
Classes:
    GPS - includes functions:
        lla2ecef
        ecef2lla
    WGS84 - constant parameters for GPS class
"""
# Import required packages
from math import sqrt, sin, cos, tan, atan, atan2
from numpy import array, dot
import GNSS.geo as geo


class WGS84:
    """
    General parameters defined by the WGS84 system
    """

    a = 6378137.0                       # Semimajor axis length (m)
    b = 6356752.3142                    # Semiminor axis length (m)
    f = (a - b) / a                     # Ellipsoid flatness (unitless)
    e = sqrt(f * (2 - f))               # Eccentricity (unitless)
    c = 299792458.                      # Speed of light (m/s)
    F = -4.442807633e-10                # Relativistic constant
    mu = 3.986005e14                    # Earth's universal gravitational constant
    omega_ie = 7.2921151467e-5          # Earth rotation rate (rad/s)

    def g0(self, L):
        """
        acceleration due to gravity at the elipsoid surface at latitude L
        """
        return 9.7803267715 * (1 + 0.001931851353 * sin(L)**2) / \
            sqrt(1 - 0.0066943800229 * sin(L)**2)

    def lla2ecef(self, lla):
        """
        Convert lat, lon, alt to Earth-centered, Earth-fixed coordinates.
        Input: lla - (lat, lon, alt) in (decimal degrees, decimal degees, m)
        Output: ecef - (x, y, z) in (m, m, m)
        """
        # Decompose the input
        lat = geo.deg2rad(lla[0])
        lon = geo.deg2rad(lla[1])
        alt = lla[2]
        # Calculate length of the normal to the ellipsoid
        N = self.a / sqrt(1 - (self.e * sin(lat))**2)
        # Calculate ecef coordinates
        x = (N + alt) * cos(lat) * cos(lon)
        y = (N + alt) * cos(lat) * sin(lon)
        z = (N * (1 - self.e**2) + alt) * sin(lat)
        # Return the ecef coordinates
        return (x, y, z)

    def lla2gcc(self, lla, geoOrigin=''):
        """
        lla2gcc converts
        """
        if geoOrigin:
            lon0, lat0, a0 = [float(c) for c in geoOrigin.split()]
            x0, y0, z0 = self.lla2ecef((lat0, lon0, a0))
        else:
            x0, y0, z0 = 0, 0, 0

        x, y, z = self.lla2ecef(lla)

        return (x - x0, y - y0, z - z0)

    def ecef2lla(self, ecef, tolerance=1e-9):
        """
        Convert Earth-centered, Earth-fixed coordinates to lat, lon, alt.
        Input: ecef - (x, y, z) in (m, m, m)
        Output: lla - (lat, lon, alt) in (decimal degrees, decimal degrees, m)
        """
        # Decompose the input
        x = ecef[0]
        y = ecef[1]
        z = ecef[2]
        # Calculate lon
        lon = atan2(y, x)
        # Initialize the variables to calculate lat and alt
        alt = 0
        N = self.a
        p = sqrt(x**2 + y**2)
        lat = 0
        previousLat = 90
        # Iterate until tolerance is reached
        while abs(lat - previousLat) >= tolerance:
            previousLat = lat
            sinLat = z / (N * (1 - self.e**2) + alt)
            lat = atan((z + self.e**2 * N * sinLat) / p)
            N = self.a / sqrt(1 - (self.e * sinLat)**2)
            alt = p / cos(lat) - N
        # Return the lla coordinates
        return (geo.rad2deg(lat), geo.rad2deg(lon), alt)

    def ecef2ned(self, ecef, origin):
        """
        Converts ecef coordinates into local tangent plane where the
        origin is the origin in ecef coordinates.
        Input: ecef - (x, y, z) in (m, m, m)
            origin - (x0, y0, z0) in (m, m, m)
        Output: ned - (north, east, down) in (m, m, m)
        """
        # print('ecef = ', ecef)
        # print('origin = ', origin)

        llaOrigin = self.ecef2lla(origin)
        lat = geo.deg2rad(llaOrigin[0])
        lon = geo.deg2rad(llaOrigin[1])
        Re2t = array([[-sin(lat)*cos(lon), -sin(lat)*sin(lon), cos(lat)],
                      [-sin(lon), cos(lon), 0],
                      [-cos(lat)*cos(lon), -cos(lat)*sin(lon), -sin(lat)]])

        # print('type ecef = %s' % type(ecef))
        # print('type origin = %s' % type(origin))

        return list(dot(Re2t, array(ecef) - array(origin)))

    def ned2ecef(self, ned, origin):
        """
        Converts ned local tangent plane coordinates into ecef coordinates
        using origin as the ecef point of tangency.
        Input: ned - (north, east, down) in (m, m, m)
            origin - (x0, y0, z0) in (m, m, m)
        Output: ecef - (x, y, z) in (m, m, m)
        """
        llaOrigin = self.ecef2lla(origin)
        lat = geo.deg2rad(llaOrigin[0])
        lon = geo.deg2rad(llaOrigin[1])
        Rt2e = array([[-sin(lat)*cos(lon), -sin(lon), -cos(lat)*cos(lon)],
                      [-sin(lat)*sin(lon), cos(lon), -cos(lat)*sin(lon)],
                      [cos(lat), 0., -sin(lat)]])
        return list(dot(Rt2e, array(ned)) + array(origin))

    def ned2pae(self, ned):
        """
        Converts the local north, east, down coordinates into range, azimuth,
        and elevation angles
        Input: ned - (north, east, down) in (m, m, m)
        Output: pae - (p, alpha, epsilon) in (m, degrees, degrees)
        """
        p = geo.euclideanDistance(ned)
        alpha = atan2(ned[1], ned[0])
        epsilon = atan2(-ned[2], sqrt(ned[0]**2 + ned[1]**2))
        return [p, geo.rad2deg(alpha), geo.rad2deg(epsilon)]

    def ecef2pae(self, ecef, origin):
        """
        Converts the ecef coordinates into a tangent plane with the origin
        privided, returning the range, azimuth, and elevation angles.
        This is a convenience function combining ecef2ned and ned2pae.
        Input: ecef - (x, y, z) in (m, m, m)
            origin - (x0, y0, z0) in (m, m, m)
        Output: pae - (p, alpha, epsilon) in (m, degrees, degrees)
        """
        ned = self.ecef2ned(ecef, origin)
        return self.ned2pae(ned)

    def ecef2utm(self, ecef):
        """
        ecef2utm converts ECEF to UTM
        """
        lla = self.ecef2lla(ecef)
        utm, info = self.lla2utm(lla)
        return utm, info

    def lla2utm(self, lla):
        """
        Converts lat, lon, alt to Universal Transverse Mercator coordinates
        Input: lla - (lat, lon, alt) in (decimal degrees, decimal degrees, m)
        Output: utm - (easting, northing, upping) in (m, m, m)
            info - (zone, scale factor)
        Algorithm from:
            Snyder, J. P., Map Projections-A Working Manual, U.S. Geol. Surv.
                Prof. Pap., 1395, 1987
        Code segments from pygps project, Russ Nelson
        """
        # Decompose lla
        lat = lla[0]
        lon = lla[1]
        alt = lla[2]
        # Determine the zone number
        zoneNumber = int((lon+180.)/6) + 1
        # Special zone for Norway
        if (56. <= lat < 64.) and (3. <= lon < 12.):
            zoneNumber = 32
        # Special zones for Svalbard
        if 72. <= lat < 84.:
            if 0. <= lon < 9.:
                zoneNumber = 31
            elif 9. <= lon < 21.:
                zoneNumber = 33
            elif 21. <= lon < 33.:
                zoneNumber = 35
            elif 33. <= lon < 42.:
                zoneNumber = 37
        # Format the zone
        zone = "%d%c" % (zoneNumber, self.utmLetterDesignator(lat))
        # Determine longitude origin
        lonOrigin = (zoneNumber - 1) * 6 - 180 + 3
        # Convert to radians
        latRad = geo.deg2rad(lat)
        lonRad = geo.deg2rad(lon)
        lonOriginRad = geo.deg2rad(lonOrigin)
        # Conversion constants
        k0 = 0.9996
        eSquared = self.e**2
        ePrimeSquared = eSquared/(1.-eSquared)
        N = self.a/sqrt(1.-eSquared*sin(latRad)**2)
        T = tan(latRad)**2
        C = ePrimeSquared*cos(latRad)**2
        A = (lonRad - lonOriginRad)*cos(latRad)
        M = self.a*(
            (1. -
                eSquared/4. -
                3.*eSquared**2/64. -
                5.*eSquared**3/256)*latRad -
            (3.*eSquared/8. +
                3.*eSquared**2/32. +
                45.*eSquared**3/1024.)*sin(2.*latRad) +
            (15.*eSquared**2/256. +
                45.*eSquared**3/1024.)*sin(4.*latRad) -
            (35.*eSquared**3/3072.)*sin(6.*latRad))
        M0 = 0.
        # Calculate coordinates
        x = k0*N*(
            A+(1-T+C)*A**3/6. +
            (5.-18.*T+T**2+72.*C-58.*ePrimeSquared)*A**5/120.) + 500000.
        y = k0*(
            M-M0+N*tan(latRad)*(
                A**2/2. +
                (5.-T+9.*C+4.*C**2)*A**4/24. +
                (61.-58.*T+T**2+600.*C-330.*ePrimeSquared)*A**6/720.))
        # Calculate scale factor
        k = k0*(1 +
                (1+C)*A**2/2. +
                (5.-4.*T+42.*C+13.*C**2-28.*ePrimeSquared)*A**4/24. +
                (61.-148.*T+16.*T**2)*A**6/720.)
        utm = [x, y, alt]
        info = [zone, k]
        return utm, info

    def utmLetterDesignator(self, lat):
        """
        Returns the latitude zone of the UTM coordinates
        """
        if -80 <= lat < -72:
            return 'C'
        elif -72 <= lat < -64:
            return 'D'
        elif -64 <= lat < -56:
            return 'E'
        elif -56 <= lat < -48:
            return 'F'
        elif -48 <= lat < -40:
            return 'G'
        elif -40 <= lat < -32:
            return 'H'
        elif -32 <= lat < -24:
            return 'J'
        elif -24 <= lat < -16:
            return 'K'
        elif -16 <= lat < -8:
            return 'L'
        elif -8 <= lat < 0:
            return 'M'
        elif 0 <= lat < 8:
            return 'N'
        elif 8 <= lat < 16:
            return 'P'
        elif 16 <= lat < 24:
            return 'Q'
        elif 24 <= lat < 32:
            return 'R'
        elif 32 <= lat < 40:
            return 'S'
        elif 40 <= lat < 48:
            return 'T'
        elif 48 <= lat < 56:
            return 'U'
        elif 56 <= lat < 64:
            return 'V'
        elif 64 <= lat < 72:
            return 'W'
        elif 72 <= lat < 80:
            return 'X'
        else:
            return 'Z'

    def decimalDegrees2DMS(self, value, type):
        """
        Converts a Decimal Degree Value into
        Degrees Minute Seconds Notation.

        Pass value as double
        type = {Latitude or Longitude} as string

        returns a string as D:M:S:Direction
        created by: anothergisblog.blogspot.com
        """
        degrees = int(value)
        submin = abs((value - int(value)) * 60)
        minutes = int(submin)
        subseconds = abs((submin-int(submin)) * 60)
        direction = ""
        if type == "Longitude":
            if degrees < 0:
                direction = "W"
            elif degrees > 0:
                direction = "E"
            else:
                direction = ""
        elif type == "Latitude":
            if degrees < 0:
                direction = "S"
            elif degrees > 0:
                direction = "N"
            else:
                direction = ""
        notation = str(degrees) + ":" + str(minutes) + ":" + str(subseconds)[0:5] + "" + direction
        return notation

    def decimalDegrees2DM(self, value):
        """
        Converts a Decimal Degree Value into
        Degrees Minute Notation.

        Pass value as double

        returns a string as D:M
        created by: anothergisblog.blogspot.com
        adopted by: alain.muls@gmail.com
        """
        degrees = int(value)
        minutes = abs((value - int(value)) * 60)

        notation = str(degrees) + "," + str(minutes)
        return notation

if __name__ == "__main__":
    wgs84 = WGS84()

    lla = (34. + 0/60. + 0.00174/3600.,               # Lat = 34d....
           -117. - 20./60. - 0.84965/3600.,           # Lon = -117d....
           251.702)                                   # ellH = 251.702
    print("lla: ", lla)
    ecef = wgs84.lla2ecef(lla)
    print("ecef: ", ecef)
    print("lla: ", wgs84.ecef2lla(ecef))

    rma = (50.843974646, 4.392840242, 146.8833)
    ecef = wgs84.lla2ecef(rma)
    print("RMA ecef: ", ecef)
    print("RMA  lla: ", wgs84.ecef2lla(ecef))

    begpRefPos = (4023741.3002569391, 309110.46204626531, 4922723.1941285301)
    begpt = (4023741.2986829998, 309110.46863399999, 4922723.1883859998)

    enu = wgs84.ecef2ned(begpt, begpRefPos)
    print('TURP @t: ', begpt)
    print('RefPos : ', begpRefPos)
    print('ENU    : ', enu)

    utm = wgs84.lla2utm(lla)
    print('utm    : ', utm)
