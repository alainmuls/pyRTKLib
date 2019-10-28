#!/bin/bash

pyrtkproc.py -d ~/RxTURP/BEGPIOS/BEGP/rinex/19125 -r BEGP1250.19o -f 4 -m single -c 5 -e rnx/igs20516.sp3 rnx/igs20520.sp3 rnx/igs20521.sp3 -g gal -t ~/amPython/pyRTKLib/rnx2rtkp.tmpl -i brdc -a saas -s precise -v -o
