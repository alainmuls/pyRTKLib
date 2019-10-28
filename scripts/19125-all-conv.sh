#!/bin/bash

pyconvbin.py -d ~/RxTURP/BEGPIOS/ASTX/19125/ -f SEPT1250.19_ -b SBF -v R3 -r ~/RxTURP/BEGPIOS/ASTX/rinex/19125/ -n GALI 125 19 -o -g gal

pyconvbin.py -d ~/RxTURP/BEGPIOS/ASTX/19125/ -f SEPT1250.19_ -b SBF -v R3 -r ~/RxTURP/BEGPIOS/ASTX/rinex/19125/ -n GPSS 125 19 -o -g gps

pyconvbin.py -d ~/RxTURP/BEGPIOS/ASTX/19125/ -f SEPT1250.19_ -b SBF -v R3 -r ~/RxTURP/BEGPIOS/ASTX/rinex/19125/ -n COMB 125 19 -o -g com
