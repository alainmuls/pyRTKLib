# print DOY with leading zeros if needed
function leading_zero()
{
    local num=$1
    local zeroos=000
    echo ${zeroos:${#num}:${#zeroos}}${num}
}

function cleanup()
{
	printf '\n'
	if [[ '${CURBRANCH}' != 'master' ]]
	then
		${GIT} checkout ${CURBRANCH}  --quiet
	fi
	cd ${OLDPWD}
}

# set the python virtual environment
PROJECT_NAME=${PYVENV}
GIT_BRANCH=${BRANCH}
VIRTUAL_ENV=${WORKON_HOME}/${PROJECT_NAME}
PYHOMEDIR=${PROJECT_HOME}/${PROJECT_NAME}

# set the start directory
RXTURPROOT=${HOME}/RxTURP/BEGPIOS
# file with directories containing Raw SBF data
GNSSRAWDATA=${RXTURPROOT}/gnss_raw_data.t

# commands
AWK=/usr/bin/awk
CP=/bin/cp
GIT=/usr/bin/git
GREP=/bin/grep
NICE='/usr/bin/nice -n 19'
RM=/bin/rm
SED=/bin/sed
SORT=/usr/bin/sort
TOUCH=/usr/bin/touch
TR=/usr/bin/tr

# pythonscripts
PYSBFDAILY=${PYHOMEDIR}/pySBFDaily.py
PYCONVBIN=${PYHOMEDIR}/pyconvbin.py
PYFTPOSNAV=${PYHOMEDIR}/pyftposnav.py
PYRTKPROC=${PYHOMEDIR}/pyrtkproc.py
PYRTKPLOT=${PYHOMEDIR}/pyrtkplot.py
PYPOS2MAVG=${PYHOMEDIR}/pos2movavg.py

# log files
LOGPYRTKPROC=${PYHOMEDIR}/pyrtkproc.log
LOGPYRTKPLOT=${PYHOMEDIR}/pyrtkplot.log

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
if [ '${CURBRANCH}' != ${GIT_BRANCH} ]
then
	${GIT} checkout ${GIT_BRANCH} --quiet
	WORKBRANCH=`${GIT} branch | ${GREP} ^* | ${TR} -d '*'`
fi

# source for activating the selected python virtual environment
source ${VIRTUAL_ENV}/bin/activate
printf '\nActivated python virtual environment '${PROJECT_HOME}/${PROJECT_NAME}'\n'
printf '            git branch '${GIT_BRANCH}'\n'

echo '-------------------------------------------------'
echo 'VIRTUAL_ENV = '${VIRTUAL_ENV}
echo 'PROJECT_NAME = '${PROJECT_NAME}
echo 'CURBRANCH = '${CURBRANCH}
echo 'WORKBRANCH = '${WORKBRANCH}
echo
echo 'PYHOMEDIR = '${PYHOMEDIR}
echo 'PYSBFDAILY = '${PYSBFDAILY}
echo 'RXTURPROOT = '${RXTURPROOT}
echo 'PYCONVBIN = '${PYCONVBIN}

echo 'PYFTPOSNAV = '${PYFTPOSNAV}
echo 'PYRTKPROC = '${PYRTKPROC}
echo 'PYRTKPLOT = '${PYRTKPLOT}
echo 'PYPOS2MAVG = '${PYPOS2MAVG}
echo
echo 'GNSSRAWDATA = '${GNSSRAWDATA}
echo '-------------------------------------------------'
