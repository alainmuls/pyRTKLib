# print DOY with leading zeros if needed
function leading_zero()
{
    local num=$1
    local zeroos=000
    echo ${zeroos:${#num}:${#zeroos}}${num}
}

function cleanup()
{
	cd ${PYHOMEDIR}
	printf '\n'
	echo 'in cleanup'
	if [[ '${CURBRANCH}' != 'master' ]]
	then
		${GIT} checkout ${CURBRANCH}
	fi
	cd ${OLDPWD}
}

# set the python virtual environment
PROJECT_NAME=${PYVENV}
VIRTUAL_ENV=${WORKON_HOME}/${PROJECT_NAME}
PYHOMEDIR=${PROJECT_HOME}/${PROJECT_NAME}

# set the start directory
RXTURPROOT=${HOME}/RxTURP/BEGPIOS

# commands
GIT=/usr/bin/git
GREP=/bin/grep
TR=/usr/bin/tr
NICE='/usr/bin/nice -n 19'
TOUCH=/usr/bin/touch
SED=/bin/sed

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
igsNavCountry=([0]='BEL' [1]='BEL' [2]='IGS')
igsNavNameExt=([0]='E' [1]='G' [2]='M')

# make sure to be on the master branch
OLDPWD=`pwd`
cd ${PYHOMEDIR}
CURBRANCH=`${GIT} branch | ${GREP} ^* | ${TR} -d '*'`
if [ '${CURBRANCH}' != 'master' ]
then
	${GIT} checkout master
fi

# source for activating the selected python virtual environment
source ${VIRTUAL_ENV}/bin/activate
printf '\nActivated python virtual environment '${PROJECT_HOME}/${PROJECT_NAME}'\n'


echo '-------------------------------------------------'
echo 'VIRTUAL_ENV = '${VIRTUAL_ENV}
echo 'PROJECT_NAME = '${PROJECT_NAME}
echo 'CURBRANCH = '${CURBRANCH}
echo
echo 'PYHOMEDIR = '${PYHOMEDIR}
echo 'PYSBFDAILY = '${PYSBFDAILY}
echo 'RXTURPROOT = '${RXTURPROOT}
echo 'PYCONVBIN = '${PYCONVBIN}
echo 'PYFTPOSNAV = '${PYFTPOSNAV}
echo 'PYRTKPROC = '${PYRTKPROC}
echo 'PYRTKPLOT = '${PYRTKPLOT}
echo 'PYPOS2MAVG = '${PYPOS2MAVG}
echo '-------------------------------------------------'
