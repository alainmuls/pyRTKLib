# constants used for parsing the status file of RTKLib

# create a dictionary with the data used for parsing a RTKLib status file
dRTKPosStat = {}

# subdict for reading SAT status part
dResiduals = {}
dResiduals['colNames'] = ('ID', 'WNC', 'TOW', 'SV', 'Freq', 'Azim', 'Elev', 'PRres', 'CFres', 'Valid', 'CN0', 'FIX', 'Slip', 'lock', 'OutageCount', 'SlipCount', 'OutlierCount')
dResiduals['useCols'] = ('WNC', 'TOW', 'SV', 'Freq', 'Azim', 'Elev', 'PRres', 'CFres', 'Valid', 'CN0')

dCartesian = {}
dCartesian['colNames'] = ('ID', 'WNC', 'TOW', 'mode', 'X', 'Y', 'Z', 'Xfix', 'Yfix', 'Zfix')
dCartesian['useCols'] = ('WNC', 'TOW', 'mode', 'X', 'Y', 'Z', 'Xfix', 'Yfix', 'Zfix')

dClock = {}
dClock['colNames'] = ('ID', 'WNC', 'TOW', 'mode', 'rcv', 'GPS', 'GLO', 'GAL', 'OTH')
dClock['useCols'] = ('WNC', 'TOW', 'mode', 'rcv', 'GPS', 'GLO', 'GAL', 'OTH')

# add subdicts to dRTKPosStat
dRTKPosStat['Res'] = dResiduals
dRTKPosStat['Cart'] = dCartesian
dRTKPosStat['Clk'] = dClock

# links between the text and numeric values used by RTKLIB
# Positioning mode
dPosMode = {0: 'single', 1: 'dgps', 2: 'kinematic', 3: 'static', 4: 'moving-base', 5: 'fixed', 6: 'ppp-kinematic', 7: 'ppp-static'}

dRTKQual = {1: 'fix', 2: 'float', 3: 'sbas', 4: 'dgps', 5: 'single', 6: 'ppp'}

dFreq = {1: 'l1', 2: 'l1+l2', 3: 'l1+l2+l5', 4: 'l1+l2+l5+l6', 5: 'l1+l2+l5+l6+l7'}

dTropo = {0: 'off', 1: 'saas', 2: 'sbas', 3: 'est-ztd', 4: 'est-ztdgrad'}

dIono = {0: 'off', 1: 'brdc', 2: 'sbas', 3: 'dual-freq', 4: 'est-stec', 5: 'ionex-tec', 6: 'qzs-brdc', 7: 'qzs-lex', 8: 'vtec_sf', 9: 'vtec_ef', 10: 'gtec'}

dSatEph = {0: 'brdc', 1: 'precise', 2: 'brdc+sbas', 3: 'brdc+ssrapc', 4: 'brdc+ssrcom'}

dNavSys = {1: 'gps', 2: 'sbas', 4: 'glo', 8: 'gal', 9: 'com', 16: 'qzs', 32: 'comp'}

dSolFormat = {0: 'llh', 1: 'xyz', 2: 'enu', 3: 'nmea'}

dTimeSys = {0: 'gpst', 1: 'utc', 2: 'jst'}

dOutHeight = {0: 'ellipsoidal', 1: 'geodetic'}

dDynamics = {0: 'off', 1: 'on'}
