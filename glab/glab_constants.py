import math

# constants used for parsing the gLABs out file

# colors for ENU plots
enu_colors = ['tab:green', 'tab:blue', 'tab:brown']
# enu_offsets = ['dN0', 'dE0', 'dU0']

# create the DOP bins and dop colors for plotting
dop_bins = [0, 2, 3, 4, 5, 6, math.inf]
dop_colors = ['tab:green', 'tab:orange', 'tab:blue', 'tab:purple', 'tab:red', 'tab:brown']

# Set the font dictionaries (for plot title and axis titles)
title_font = {'fontname': 'DejaVu Sans', 'size': '16', 'color': 'black', 'weight': 'heavy', 'verticalalignment': 'top'}  # Bottom vertical alignment for more space
axis_font = {'fontname': 'DejaVu Sans', 'size': '14'}


def predefined_marker_styles() -> list:
    """
    # styles used for displaying the values per PDOP bin
    predefined markerstyles for plotting
    Returns: markerBins used for coloring as function of DOP bin
    """
    # # plot the centerpoint and circle
    marker_style_doplt2 = dict(linestyle='', color='tab:green', markersize=2, marker='.', markeredgecolor='green', alpha=0.30)
    marker_style_doplt3 = dict(linestyle='', color='tab:orange', markersize=2, marker='.', markeredgecolor='orange', alpha=0.45)
    marker_style_doplt4 = dict(linestyle='', color='tab:blue', markersize=2, marker='.', markeredgecolor='blue', alpha=0.60)
    marker_style_doplt5 = dict(linestyle='', color='tab:purple', markersize=2, marker='.', markeredgecolor='purple', alpha=0.75)
    marker_style_doplt6 = dict(linestyle='', color='tab:red', markersize=2, marker='.', markeredgecolor='red', alpha=0.90)
    marker_style_dopgt6 = dict(linestyle='', color='tab:brown', markersize=2, marker='.', markeredgecolor='black', alpha=0.90)
    marker_style_center = dict(linestyle='', color='tab:red', markersize=5, marker='^', markeredgecolor='red', alpha=0.75)

    markerBins = [marker_style_doplt2, marker_style_doplt3, marker_style_doplt4, marker_style_doplt5, marker_style_doplt6, marker_style_dopgt6, marker_style_center]

    return markerBins


# create a dictionary with the column names available / used for parsing
dgLab = {}

# read in the glab_outfile and split it into its parts (stored in temporary files)
glab_msgs = ('INFO', 'OUTPUT', 'SATSEL', 'MEAS', 'MODEL', 'FILTER')
dgLab['messages'] = glab_msgs

# connect abbreviation of GNSS to the names used
dgLab['GNSS'] = {
                'E': {'marker': 'GALI', 'gnss': 'Galileo', 'color': 'blue'},
                'G': {'marker': 'GPSN', 'gnss': 'GPS NavSTAR', 'color': 'red'},
                'GE': {'marker': 'COMB', 'gnss': 'Combined GE', 'color': 'grey'},
                'EG': {'marker': 'COMB', 'gnss': 'Combined EG', 'color': 'grey'},
                }  # noqa: E123

# dgLab['GNSS'] = dGNSS

# Looking up the INFO messages
dINFO = {}

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
dINFO['summary'] = 'INFO Station'

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
dOUTPUT['ENU'] = ['UTM.N', 'UTM.E', 'ellH']

dgLab['OUTPUT'] = dOUTPUT
