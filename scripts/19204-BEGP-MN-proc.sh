#!/bin/bash

echo ${PROJECT_HOME}
echo ${PROJECT_NAME}
${PROJECT_HOME}/pyRTKLib/pyrtkproc.py -d ~/RxTURP/BEGPIOS/BEGP/rinex/19204/ -r Inte204JK.19_.obs -f 4 -m single -c 5 -e BRUX00BEL_R_20192040000_01D_EN.rnx -g gal -t ~/amPython/pyRTKLib/rnx2rtkp.tmpl -i brdc -a saas -s brdc -l INFO DEBUG -o
