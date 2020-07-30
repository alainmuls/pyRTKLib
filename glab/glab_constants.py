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

dgLab['INFO'] = dINFO

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
