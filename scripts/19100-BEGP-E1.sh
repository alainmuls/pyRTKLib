#!/bin/bash

cd ~/RxTURP/BEGPIOS/BEGP/rinex/19100/
gfzrnx -finp BEGP1000.19O -fout BEGP1000-E1.19O -f -vo 3 --obs_types C1A,L1A,D1A,S1A