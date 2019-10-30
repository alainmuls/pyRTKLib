#!/usr/bin/env python

from ftplib import FTP

ftp = FTP('cddis.gsfc.nasa.gov')
ftp.login('ftp', 'alain.muls@gmail.com')

# Get All Files
files = ['BRDC00IGS_R_20191000000_01D_MN.rnx.gz']

# Print out the files
for file in files:
    print("Downloading..." + file)
    ftp.retrbinary("RETR " + '/pub/gps/data/daily/2019/100/19p/' + file, open("/tmp/" + file, 'wb').write)

ftp.close()

print('file downloaded')
