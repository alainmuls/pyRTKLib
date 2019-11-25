# print DOY with leading zeros if needed
function leading_zero()
{
    local num=$1
    local zeroos=000
    echo ${zeroos:${#num}:${#zeroos}}${num}
}

# set the python virtual environment
PROJECT_NAME=${PYVENV}
VIRTUAL_ENV=${WORKON_HOME}/${PROJECT_NAME}
PYHOMEDIR=${PROJECT_HOME}/${PROJECT_NAME}

# set the start directory
RXTURP=${HOME}/RxTURP/BEGPIOS

# commands
GIT=/usr/bin/git
GREP=/bin/grep
TR=/usr/bin/tr
NICE='/usr/bin/nice -n 19'

# pythonscripts
PYSBFDAILY=${PYHOMEDIR}/pySBFDaily.py
PYCONVBIN=${PYHOMEDIR}/pyconvbin.py
PYFTPOSNAV=${PYHOMEDIR}/pyftposnav.py
PYRTKPROC=${PYHOMEDIR}/pyrtkproc.py
PYRTKPLOT=${PYHOMEDIR}/pyrtkplot.py
PYPOS2MAVG=${PYHOMEDIR}/pos2movavg.py

# the gnss and corresponding marker name lists
gnss=([0]='gal' [1]='gps' [2]='com')
gnssMarker=([0]='GALI' [1]='GPSS' [2]='COMB')
gnssNavExt=([0]='E' [1]='N' [2]='P')
igsNavName=([0]='BRUX' [1]='BRUX' [2]='BRDC')
igsNavNameExt=([0]='E' [1]='N' [2]='M')

# make sure to be on the master branch
CURBRANCH=`${GIT} branch | ${GREP} ^* | ${TR} -d '*'`
if [ ${CURBRANCH} != 'master' ]
then
	${GIT} checkout master
fi

# source for activating the selected python virtual environment
source ${VIRTUAL_ENV}/bin/activate
printf '\nActivated python virtual environment '${PROJECT_HOME}/${PROJECT_NAME}'\n'


echo '-------------------------------------------------'
echo 'CURBRANCH = '${CURBRANCH}
echo 'GIT = '${GIT}
echo 'GREP = '${GREP}
echo 'NICE = '${NICE}
echo 'PROJECT_NAME = '${PROJECT_NAME}
echo 'PYCONVBIN = '${PYCONVBIN}
echo 'PYFTPOSNAV = '${PYFTPOSNAV}
echo 'PYHOMEDIR = '${PYHOMEDIR}
echo 'PYPOS2MAVG = '${PYPOS2MAVG}
echo 'PYRTKPLOT = '${PYRTKPLOT}
echo 'PYRTKPROC = '${PYRTKPROC}
echo 'PYSBFDAILY = '${PYSBFDAILY}
echo 'RXTURP = '${RXTURP}
echo 'TR = '${TR}
echo 'VIRTUAL_ENV = '${VIRTUAL_ENV}
echo '-------------------------------------------------'
