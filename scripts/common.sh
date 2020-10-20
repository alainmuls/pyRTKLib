# commands
AWK=/usr/bin/awk
CP=/bin/cp
CUT=/usr/bin/cut
DU=/usr/bin/du
GIT=/usr/bin/git
GREP=/bin/grep
NICE='/usr/bin/nice -n 19'
RM=/bin/rm
SED=/bin/sed
SORT=/usr/bin/sort
TOUCH=/usr/bin/touch
TR=/usr/bin/tr

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
	if [[ '${CURBRANCH}' != '${GIT_BRANCH' ]]
	then
		${GIT} checkout ${CURBRANCH}  --quiet
	fi
	cd ${OLDPWD}
}

function escape_slashes {
    ${SED} 's/\//\\\//g'
}

function change_line {
    local OLD_LINE_PATTERN=$1; shift
    local NEW_LINE=$1; shift
    local FILE=$1

    # echo ${OLD_LINE_PATTERN}
    # echo ${NEW_LINE}
    # echo ${FILE}

    local NEW=$(echo "${NEW_LINE}" | escape_slashes)

    # /bin/sed -i "s+TURP,19,134,19134,/home/amuls/RxTURP/BEGPIOS/TURP/19134,true*+TURP,19,134,19134,\/home\/amuls\/RxTURP\/BEGPIOS\/TURP\/19134,true,GPRS1340.19O,75M,GPRS1340.19E,96K+g" /home/amuls/RxTURP/BEGPIOS/BEGP_data.t

    ${SED} -i.bak "s+${OLD_LINE_PATTERN}.*+${NEW}+g" ${FILE}
    # mv "${FILE}.bak" /tmp/
}

# set the python virtual environment
PROJECT_NAME=${PYVENV}
GIT_BRANCH=${BRANCH}
VIRTUAL_ENV=${WORKON_HOME}/${PROJECT_NAME}
PYHOMEDIR=${PROJECT_HOME}/${PROJECT_NAME}

# set the start directory
RXTURPROOT=${HOME}/RxTURP/BEGPIOS
# file with directories containing Raw SBF data
GNSSRAWDATA=${RXTURPROOT}'/'${RXTYPE}'_data.t'

# pythonscripts
PYSBFDAILY=${PYHOMEDIR}/pysbfdaily.py
GFZRNX_CONVBIN=${PYHOMEDIR}/gfzrnx_convbin.py
PYFTPOSNAV=${PYHOMEDIR}/pyftposnav.py
PYRTKPROC=${PYHOMEDIR}/pyrtkproc.py
PYRTKPLOT=${PYHOMEDIR}/pyrtkplot.py
PYPOS2MAVG=${PYHOMEDIR}/pos2movavg.py
RNX_OBS_TABULAR=${PYHOMEDIR}/rnx_obs_tabular.py

# galb related scripts
GLABPROC=${PYHOMEDIR}/glab_processing.py
GLABMSGOUTPUT=${PYHOMEDIR}/glab_msg_output.py

# log files
# LOGPYRTKPROC=${PYHOMEDIR}/pyrtkproc.log
# LOGPYRTKPLOT=${PYHOMEDIR}/pyrtkplot.log

# the gnss and corresponding marker name lists
gnss=([0]='Galileo' [1]='GPS Navstar' [2]='Combined EG')
gnssMarker=([0]='GALI' [1]='GPSN' [2]='COMB')
gnssNavExt=([0]='E' [1]='N' [2]='P')
# for IGS downloaded data
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
echo 'GFZRNX_CONVBIN = '${GFZRNX_CONVBIN}

echo 'PYFTPOSNAV = '${PYFTPOSNAV}
echo 'PYRTKPROC = '${PYRTKPROC}
echo 'PYRTKPLOT = '${PYRTKPLOT}
echo 'PYPOS2MAVG = '${PYPOS2MAVG}
echo
echo 'GNSSRAWDATA = '${GNSSRAWDATA}
echo '-------------------------------------------------'
