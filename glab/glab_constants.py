# constants used for parsing the gLABs out file

# create a dictionary with the column names available / used for parsing
dgLab = {}

# read in the glab_outfile and split it into its parts (stored in temporary files)
glab_msgs = ('INFO', 'OUTPUT', 'SATSEL', 'MEAS', 'MODEL', 'FILTER')
dgLab['messages'] = glab_msgs

# Looking up the INFO messages
dINFO = {}
dINFO['obs'] = 'INFO RINEX observation input file'
dINFO['nav'] = 'INFO RINEX navigation message input file'
dINFO['proc'] = 'INFO Processing with'
dINFO['ant_type'] = 'INFO INPUT Antenna type'
dINFO['rx_type'] = 'INFO INPUT Receiver type'
dINFO['decimation'] = 'INFO PREPROCESSING Decimation'
dINFO['freqs_gps'] = 'INFO PREPROCESSING Usable frequencies [GPS]'
dINFO['freqs_gal'] = 'INFO PREPROCESSING Usable frequencies [Galileo]'
dINFO['mask'] = 'INFO PREPROCESSING Elevation mask'
dINFO['rx_ecef'] = 'INFO PREPROCESSING Receiver a priori position (metres)'
dINFO['atm_iono'] = 'INFO MODELLING Ionosphere model'
dINFO['atm_tropo'] = 'INFO MODELLING Troposphere model'
dINFO['ref_clk'] = 'INFO FILTER Reference clock constellation priority list'
dINFO['epochs'] = 'INFO Total epochs processed'
dINFO['epochs_proc'] = 'INFO Total epochs processed with solution'
dINFO['gaps'] = 'INFO Number of data gaps in observation file (during summary period)'
dINFO['epoch_first'] = 'INFO First epoch of summary for computing positioning error percentiles'
dINFO['epoch_last'] = 'INFO Last  epoch of summary for computing positioning error percentiles'
dINFO['meas'] = 'INFO FILTER Meas'
dINFO['gnss_used'] = 'INFO Number of epochs with constellations used'
dINFO['gnss_notused'] = 'INFO Number of epochs with constellations not used'
dINFO['excluded'] = 'INFO PREPROCESSING Excluded satellites'
dINFO['freqs_order'] = 'INFO PREPROCESSING Measurement frequency filling order'
dINFO['freqs_priority'] = 'INFO PREPROCESSING Rover priority list for frequency'
dINFO['space'] = 'INFO MODELLING Broadcast message type order for orbits, clocks and DCB data'

# get the input files used
dFiles = {}
dFiles['obs'] = 'INFO RINEX observation input file'
dFiles['nav'] = 'INFO RINEX navigation message input file'
dFiles['antex'] = 'INFO ANTEX input file for satellite block type'

dINFO['files'] = dFiles

# get information about station/receiver/antenna
dRx = {}
dRx['marker'] = 'INFO INPUT Station marker'
dRx['rx'] = 'INFO INPUT Receiver type'
dRx['antenna'] = 'INFO INPUT Antenna type'

dINFO['rx'] = dRx

# get the preprocessing info
dPP = {}
dPP['mask'] = 'INFO PREPROCESSING Elevation mask'
dPP['freqs'] = 'INFO PREPROCESSING Usable frequencies'
dPP['freqs_order'] = 'INFO PREPROCESSING Measurement frequency filling order'
dPP['freqs_excluded'] = 'INFO PREPROCESSING Excluded frequencies by user'
dPP['rx_ecef'] = 'INFO PREPROCESSING Receiver a priori position (metres)'

dINFO['pp'] = dPP

# get info about modelling
dModel = {}

dModel['sv_clock'] = 'INFO MODELLING Satellite clock offset correction'
dModel['ARP'] = 'INFO MODELLING Receiver Antenna Reference Point (ARP)'
dModel['iono'] = 'INFO MODELLING Ionosphere model'
dModel['tropo'] = 'INFO MODELLING Troposphere model'
dModel['nav_msg'] = 'INFO MODELLING Broadcast message type order for orbits, clocks and DCB data'
dModel['use_health'] = "INFO MODELLING Use satellite 'SV Health' flag of navigation message"

dINFO['model'] = dModel

# get information about applied filter
dFilter = {}

dFilter['meas'] = 'INFO FILTER Meas'
dFilter['carrier_phase'] = 'INFO FILTER Carrierphase is used'
dFilter['tropo_estimate'] = 'INFO FILTER Estimate troposphere'
dFilter['ref_clk'] = 'INFO FILTER Reference clock constellation priority list'
dFilter['HDOP'] = 'INFO FILTER HDOP'
dFilter['PDOP'] = 'INFO FILTER PDOP'
dFilter['GDOP'] = 'INFO FILTER GDOP'

dINFO['filter'] = dFilter

# get info from summary
dSum = {}
dSum['epoch_first'] = 'INFO First epoch of summary'
dSum['epoch_last'] = 'INFO Last  epoch of summary'

dINFO['summary'] = dSum

# put all in what we want to parse from the INFO messages
dgLab['parse'] = dINFO

# the OUTPUT message field
dOUTPUT = {}
dOUTPUT['columns'] = ['OUTPUT', 'Year', 'DoY', 'sod', 'Time', 'mode', 'dir', '#SVs', '#GNSSs', 'GNSSs', 'conv', 'X', 'Y', 'Z', 'dX0', 'dY0', 'dZ0', 'sdX', 'sdY', 'sdZ', 'lat', 'lon', 'ellH', 'dN0', 'dE0', 'dU0', 'sdN', 'sdE', 'sdU', 'dplan0', 'dvert0', 'd3D', 'ref_clk', 'rx_clk', 'drx_clk', 'GDOP', 'PDOP', 'TDOP', 'HDOP', 'VDOP', 'ZTD1', 'ZTD2', 'ZTD3']
dOUTPUT['use_cols'] = dOUTPUT['columns'][1:11] + dOUTPUT['columns'][20:]
dOUTPUT['gnss'] = dOUTPUT['columns'][7:11]
dOUTPUT['llh'] = dOUTPUT['columns'][20:23]
dOUTPUT['dENU'] = dOUTPUT['columns'][23:26]
dOUTPUT['sdENU'] = dOUTPUT['columns'][26:29]
dOUTPUT['HV3D'] = dOUTPUT['columns'][29:32]
dOUTPUT['CLK'] = dOUTPUT['columns'][32:35]
dOUTPUT['XDOP'] = dOUTPUT['columns'][35:40]
dOUTPUT['ZTD'] = dOUTPUT['columns'][40:43]
dOUTPUT['UTM'] = ['UTM.N', 'UTM.E']

dgLab['OUTPUT'] = dOUTPUT
