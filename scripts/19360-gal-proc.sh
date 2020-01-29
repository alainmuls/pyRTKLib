#!/bin/bash

pyrtkproc.py -d ~/RxTURP/BEGPIOS/ASTX/rinex/19360/ -r GALI3600.19O -f 4 -m single -c 5 -e GALI3600.19E -g gal  -t ~/amPython/pyRTKLib/rnx2rtkp.tmpl -i brdc -a saas -s brdc -o -l INFO DEBUG
