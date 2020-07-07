# constants used for parsing the gLABs out file

# create a dictionary with the column names available / used for parsing
dgLab = {}

dOUTPUT = {}
dOUTPUT['columns'] = ('OUTPUT', 'Year', 'DoY', 'sod', 'Time', 'mode', 'dir', '#SVs', '#GNSSs', 'GNSSs', 'conv', 'X', 'Y', 'Z', 'dX0', 'dY0', 'dZ0', 'sdX', 'sdY', 'sdZ', 'lat', 'lon', 'ellH', 'dN0', 'dE0', 'dU0', 'sdN', 'sdE', 'sdU', 'dplan0', 'dvert0', 'd3D', 'ref_clk', 'rx_clk', 'drx_clk', 'GDOP', 'PDOP', 'TDOP', 'HDOP', 'VDOP', 'ZTD1', 'ZTD2', 'ZTD3')
dOUTPUT['use_cols'] = ('Year', 'DoY', 'sod', 'Time', 'mode', 'dir', '#SVs', '#GNSSs', 'GNSSs', 'conv', 'lat', 'lon', 'ellH', 'dN0', 'dE0', 'dU0', 'sdN', 'sdE', 'sdU', 'dplan0', 'dvert0', 'd3D', 'ref_clk', 'rx_clk', 'drx_clk', 'GDOP', 'PDOP', 'TDOP', 'HDOP', 'VDOP', 'ZTD1', 'ZTD2', 'ZTD3')

dgLab['OUTPUT'] = dOUTPUT
