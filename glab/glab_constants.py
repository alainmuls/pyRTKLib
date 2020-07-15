# constants used for parsing the gLABs out file

# create a dictionary with the column names available / used for parsing
dgLab = {}

# read in the glab_outfile and split it into its parts (stored in temporary files)
glab_msgs = ('INFO', 'OUTPUT', 'SATSEL', 'MEAS', 'MODEL', 'FILTER')
dgLab['messages'] = glab_msgs

# the OUTPUT message field
dOUTPUT = {}
dOUTPUT['columns'] = ('OUTPUT', 'Year', 'DoY', 'sod', 'Time', 'mode', 'dir', '#SVs', '#GNSSs', 'GNSSs', 'conv', 'X', 'Y', 'Z', 'dX0', 'dY0', 'dZ0', 'sdX', 'sdY', 'sdZ', 'lat', 'lon', 'ellH', 'dN0', 'dE0', 'dU0', 'sdN', 'sdE', 'sdU', 'dplan0', 'dvert0', 'd3D', 'ref_clk', 'rx_clk', 'drx_clk', 'GDOP', 'PDOP', 'TDOP', 'HDOP', 'VDOP', 'ZTD1', 'ZTD2', 'ZTD3')
dOUTPUT['use_cols'] = ('Year', 'DoY', 'sod', 'Time', 'mode', 'dir', '#SVs', '#GNSSs', 'GNSSs', 'conv', 'lat', 'lon', 'ellH', 'dN0', 'dE0', 'dU0', 'sdN', 'sdE', 'sdU', 'dplan0', 'dvert0', 'd3D', 'ref_clk', 'rx_clk', 'drx_clk', 'GDOP', 'PDOP', 'TDOP', 'HDOP', 'VDOP', 'ZTD1', 'ZTD2', 'ZTD3')
dOUTPUT['llh'] = ('lat', 'lon', 'ellH')
dOUTPUT['dENU'] = ('dN0', 'dE0', 'dU0')
dOUTPUT['sdENU'] = ('sdN', 'sdE', 'sdU')
dOUTPUT['xDOP'] = ('GDOP', 'PDOP', 'TDOP', 'HDOP', 'VDOP')
dOUTPUT['gnss'] = ('#SVs', '#GNSSs', 'GNSSs')

dgLab['OUTPUT'] = dOUTPUT

# Looking up the INFO messages
dINFO = {}
dINFO['obs'] = 'INFO RINEX observation input file'
dINFO['nav'] = 'INFO RINEX navigation message input file'
dINFO['marker'] = 'INFO INPUT Station marker'
dINFO['ant_type'] = 'INFO INPUT Antenna type'
dINFO['rx_type'] = 'INFO INPUT Receiver type'
dINFO['decimation'] = 'INFO PREPROCESSING Decimation'
dINFO['gps_freqs'] = 'INFO PREPROCESSING Usable frequencies [GPS]'
dINFO['gal_freqs'] = 'INFO PREPROCESSING Usable frequencies [Galileo]'
dINFO['mask'] = 'INFO PREPROCESSING Elevation mask'
dINFO['rx_ecef'] = 'INFO PREPROCESSING Receiver a priori position (metres)'
dINFO['iono'] = 'INFO FILTER Carrierphase is used'
dINFO['tropo'] = 'INFO FILTER Estimate troposphere'
dINFO['ref_clk'] = 'INFO FILTER Reference clock constellation priority list'
dINFO['epochs'] = 'INFO Total epochs processed'
dINFO['epochs_proc'] = 'INFO Total epochs processed with solution'
dINFO['gaps'] = 'INFO Number of data gaps in observation file (during summary period)'
dINFO['epoch_first'] = 'INFO First epoch of summary for computing positioning error percentiles'
dINFO['epoch_last'] = 'INFO Last  epoch of summary for computing positioning error percentiles'
dINFO['meas'] = 'INFO FILTER Meas'
dINFO['gnss_used'] = 'INFO Number of epochs with constellations used'
dINFO['gnss_notused'] = 'INFO Number of epochs with constellations not used'

dgLab['INFO'] = dINFO
