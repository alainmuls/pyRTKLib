#!/bin/bash

pyrtkproc.py -d ~/RxTURP/BEGPIOS/BEGP/rinex/19134/ -r BEGP1340.19O -f 4 -m single -c 5 -e /home/amuls/RxTURP/BEGPIOS/BEGP/igs/19134/BRUX00BEL_R_20191340000_01D_GN.rnx.gz  -g gal  -t ~/amPython/pyRTKLib/rnx2rtkp.tmpl -i brdc -a saas -s brdc -o -l INFO DEBUG
