# `pyRTKLib` repository

## Introduction

The `pyRTKLib` repository processes `RINEX` observation / navigation files for Galileo, GPS or a combination of both, using the open source [`RTKLib`](http://www.rtklib.com/) library. It generates plots for:

- `UTM` and height coordinates versus time,
- `UTM` scatter plot,
- pseudo-range residuals plot,
- Carrier-to-Noise `CN0` plot,
- satellite elevation plot, and
- receiver clock plot.

The repository is based on the following directory structure[^1] for the binary receiver data:

```bash
${HOME}/RxTURP
    BEGPIOS
        ASTX
            ...
            19133
            19134
            19135
            ...
        BEGP
            ...
            19133
            19134
            19135
            ...
        uBlox
            ...
            19133
            19134
            19135
            ...
```

where `YYDDD` represents 2 digits for the year and 3 digits for the day of year.

During processing, in each receiver type directory (`ASTX`, `BEGP`, ...) a `rinex` directory is created with sub-directories with the same `YYDDD` as the original raw binary data sub-directories.

[^1]: I never tested this repository using another directory structure.

## Processing steps

Processing is split up in 5 steps:

- __`pySBFDaily.py`__
    + receivers from Septentrio log data in the binary `SBF` format. These data are logged in (six-)hourly files and are first combined to a daily `SBF` file. The naming follows the IGS convention for `RINEX` v2.x files. The (daily) combined file is stored in the raw binary data directory.
- __`pyconvbin.py`__
    + converts the binary (daily) `SBF` or `u-Blox` file to `RINEX` observation and navigation files.
- __`pyftposnav.py`__
    + downloads the globally collected navigation file for all GNSS systems for a specific date. This creates a directory `igs` on the same level as the `rinex` directory.
- __`pyrtkproc.py`__
    + based on a common template, ensuring similar processing for all GNSSs, the `RINEX` observation and navigation files are processed using `rnx2rtkp` program from the `RTKLib` library. Two output files are created in a `rtkp`/`GNSS` subdirectory:
        * `<file-name>.pos` containing date-time, position and (co-)variance information. The processing mode and number of satellites used are also reported,
        * `<file-name>.pos.stat` containing various information about the satellites, the pseudo-range residuals, receiver clock and velocity.
- __`pyrtkplot.sh`__
    + using the `<file-name>.pos` and `<file-name>.pos.stat` files, plots are created.

Each script uses pythons logging facility and creates in the directory from which it is called a `<script-name>.log` file which can be used for later inspection. The default logging levels are:

- for the console:  `LOGGING.INFO`
- for the log-file:  `LOGGING.DEBUG`

##  __`pySBFDaily.py`__

### Getting help

```bash
$ pySBFDaily.py --help
usage: pySBFDaily.py [-h] [-d DIR] [-o]
                     [-l {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET} {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]

pySBFDaily.py creates a daily SBF file based on (six) hourly SBF files found
in given directory

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     Directory of SBF file (defaults to .)
  -o, --overwrite       overwrite daily SBF file (default False)
  -l {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET} {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}, --logging {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET} {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                        specify logging level console/file (default INFO
                        DEBUG)
```

### Processing example

```bash
$ pySBFDaily.py --dir ~/RxTURP/BEGPIOS/ASTX/19134 -o -l INFO DEBUG
INFO: pySBFDaily.py - main: working diretory is /home/amuls/RxTURP/BEGPIOS/ASTX/19134
INFO: pySBFDaily.py - main: changed to directory /home/amuls/RxTURP/BEGPIOS/ASTX/19134
INFO: pySBFDaily.py - main: combine SBF (six-)hourly files to daily SBF file
INFO: pySBFDaily.py - main: creating daily SBF file SEPT1340.19_
```

yields the following raw binary data directory:

```bash
$ ll /home/amuls/RxTURP/BEGPIOS/ASTX/19134 -rt
total 853200
-rw-rw-r-- 1 amuls amuls 100144280 May 14 08:02 SEPT1341.19_
-rw-rw-r-- 1 amuls amuls  11580873 May 14 08:02 SEPT1341.191
-rw-rw-r-- 1 amuls amuls 102000168 May 14 14:02 SEPT1342.19_
-rw-rw-r-- 1 amuls amuls  11645676 May 14 14:02 SEPT1342.191
-rw-rw-r-- 1 amuls amuls 101275596 May 14 20:02 SEPT1343.19_
-rw-rw-r-- 1 amuls amuls  11705476 May 14 20:02 SEPT1343.191
-rw-rw-r-- 1 amuls amuls  12423431 May 15 02:02 SEPT1344.191
-rw-rw-r-- 1 amuls amuls 109727776 May 15 02:02 SEPT1344.19_
-rw-r--r-- 1 amuls amuls 413147820 Oct 28 14:53 SEPT1340.19_
```

##  __`pyconvbin.py`__

### Getting help

```bash
$ pyconvbin.py --help
usage: pyconvbin.py [-h] [-d DIR] -f FILE [-b {SBF,UBlox}] [-r RINEXDIR]
                    [-v {R3,R2}] [-g {gal,gps,com}] -n NAMING NAMING NAMING
                    [-e EXPERIMENT] [-o]
                    [-l {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET} {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}]

pyconvbin.py convert binary raw data from SBF or UBlox to RINEX Obs & Nav
files

optional arguments:
  -h, --help            show this help message and exit
  -d DIR, --dir DIR     Root directory (default .)
  -f FILE, --file FILE  Binary SBF or UBlox file
  -b {SBF,UBlox}, --binary {SBF,UBlox}
                        Select binary format (default SBF)
  -r RINEXDIR, --rinexdir RINEXDIR
                        Directory for RINEX output (default .)
  -v {R3,R2}, --rinexver {R3,R2}
                        Select RINEX version (default R3)
  -g {gal,gps,com}, --gnss {gal,gps,com}
                        GNSS systems to process (default=gal)
  -n NAMING NAMING NAMING, --naming NAMING NAMING NAMING
                        Enter MARKER DOY YY for naming RINEX output files
  -e EXPERIMENT, --experiment EXPERIMENT
                        description of experiment (added to naming of RINEX
                        file)
  -o, --overwrite       overwrite intermediate files (default False)
  -l {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET} {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}, --logging {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET} {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}
                        specify logging level console/file (default INFO
                        DEBUG)
```

### Processing example

```bash
$ 19134-gal-conv.sh 
INFO: pyconvbin.py - main: arguments processed: amc.dRTK = {'rootDir': '/home/amuls/RxTURP/BEGPIOS/ASTX/19134/', 'binFile': 'SEPT1340.19_', 'binType': 'SBF', 'rinexDir': '/home/amuls/RxTURP/BEGPIOS/ASTX/rinex/19134/', 'rinexVersion': 'R3', 'gnssSyst': 'gal', 'rinexNaming': ['GALI', '134', '19'], 'experiment': ''}
INFO: pyconvbin.py - checkValidityArgs: check existence of rootDir /home/amuls/RxTURP/BEGPIOS/ASTX/19134/
INFO: pyconvbin.py - checkValidityArgs: check existence of binary file /home/amuls/RxTURP/BEGPIOS/ASTX/19134/SEPT1340.19_ to convert
INFO: pyconvbin.py - checkValidityArgs: check existence of rinexdir /home/amuls/RxTURP/BEGPIOS/ASTX/rinex/19134/ and create if needed
INFO: location.py - locateProg: locate programs convbin
INFO: location.py - locateProg: convbin is /home/amuls/bin/convbin
INFO: location.py - locateProg: locate programs sbf2rin
INFO: location.py - locateProg: sbf2rin is /home/amuls/bin/sbf2rin
INFO: pyconvbin.py - main: convert binary file to rinex
INFO: pyconvbin.py - sbf2rinex: RINEX conversion for gal
INFO: pyconvbin.py - sbf2rinex: excluding GNSS systems ['G', 'R', 'S', 'C', 'J', 'I']
INFO: pyconvbin.py - sbf2rinex: creating RINEX observation file
/home/amuls/bin/sbf2rin -f /home/amuls/RxTURP/BEGPIOS/ASTX/19134/SEPT1340.19_ -x GRSCJI -s -D -v -R3 -o /home/amuls/RxTURP/BEGPIOS/ASTX/rinex/19134/GALI1340.19O

Creating RINEX file: done                                                       
INFO: pyconvbin.py - sbf2rinex: creating RINEX navigation file
/home/amuls/bin/sbf2rin -f /home/amuls/RxTURP/BEGPIOS/ASTX/19134/SEPT1340.19_ -x GRSCJI -s -D -v -n E -R3 -o /home/amuls/RxTURP/BEGPIOS/ASTX/rinex/19134/GALI1340.19E

Creating RINEX file: done                                                       
INFO: pyconvbin.py - main: amc.dRTK =
{
    "rootDir": "/home/amuls/RxTURP/BEGPIOS/ASTX/19134/",
    "binFile": "/home/amuls/RxTURP/BEGPIOS/ASTX/19134/SEPT1340.19_",
    "binType": "SBF",
    "rinexDir": "/home/amuls/RxTURP/BEGPIOS/ASTX/rinex/19134/",
    "rinexVersion": "R3",
    "gnssSyst": "gal",
    "rinexNaming": [
        "GALI",
        "134",
        "19"
    ],
    "experiment": "",
    "marker": "GALI",
    "doy": "134",
    "yy": "19",
    "bin2rnx": {
        "CONVBIN": "/home/amuls/bin/convbin",
        "SBF2RIN": "/home/amuls/bin/sbf2rin"
    },
    "obs": "/home/amuls/RxTURP/BEGPIOS/ASTX/rinex/19134/GALI1340.19O",
    "nav": "/home/amuls/RxTURP/BEGPIOS/ASTX/rinex/19134/GALI1340.19E"
}
```

creates the following directories and files:[^2]

```bash
$ ll /home/amuls/RxTURP/BEGPIOS/ASTX/rinex/19134/
total 95808
-rw-r--r-- 1 amuls amuls   565703 Oct 28 15:04 GALI1340.19E
-rw-r--r-- 1 amuls amuls 97537766 Oct 28 15:04 GALI1340.19O
```

### Remark

The conversion for `u-Blox` receivers is still to be done.

[^2]: Depending on the selected `GNSS`, the station name is `GALI` (Galileo only), `GPSS` (GPS only) or `COMB` (Galileo and GPS combined) for the free available signals.


