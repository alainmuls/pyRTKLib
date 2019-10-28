#!/bin/bash

pyrtkproc.py -d ~/RxTURP/BEGPIOS/BEGP/rinex/19125 -r BEGP1250.19o -f 4 -m single -c 5 -e BEGP1250.19E -g gal -t ~/amPython/pyRTKLib/rnx2rtkp.tmpl -i brdc -a saas -s brdc -l INFO DEBUG -o
