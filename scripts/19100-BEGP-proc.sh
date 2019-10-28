#!/bin/bash

pyrtkproc.py -d ~/RxTURP/BEGPIOS/BEGP/rinex/19100 -r BEGP1000.19O -f 4 -m single -c 5 -e /tmp/BRDC00IGS_R_20191000000_01D_MN.rnx.gz -g gal -t ~/amPython/pyRTKLib/rnx2rtkp.tmpl -i brdc -a saas -s brdc -l INFO DEBUG -o
