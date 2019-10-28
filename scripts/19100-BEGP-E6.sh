#!/bin/bash

cd ~/RxTURP/BEGPIOS/BEGP/rinex/19100/
gfzrnx -finp BEGP1000.19O -fout BEGP1000-E6.19O -f -vo 3 --obs_types C6A,L6A,D6A,S6A