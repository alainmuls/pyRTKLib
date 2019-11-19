#!/usr/bin/env bash

STDOY=109
ENDOY=110
YY=19

function leading_zero()
{
    local num=$1
    local zeroos=000
    echo ${zeroos:${#num}:${#zeroos}}${num}
}

# set the python virtual environment
PROJECT_NAME=pyRTKLib
VIRTUAL_ENV=${WORKON_HOME}/${PROJECT_NAME}
PYHOMEDIR=${PROJECT_HOME}/${PROJECT_NAME}
# echo ${VIRTUAL_ENV}

# set the start directory
RXTURP=${HOME}/RxTURP/BEGPIOS

# commands
GIT=/usr/bin/git

# make sure to be on the master branch
${GIT} checkout master
${GIT} branch

echo 'Activating the python virtual environment '${PROJECT_HOME}/${PROJECT_NAME}
source ${VIRTUAL_ENV}/bin/activate

# ${PYHOMEDIR}/pySBFDaily.py -h

for DOY in $(seq $STDOY $ENDOY)
do
	YYDOY=${YY}`leading_zero ${DOY}`
	echo 'Creating daily file for '${YYDOY}
	${PYHOMEDIR}/pySBFDaily.py -d ${RXTURP}/ASTX/${YYDOY}
done
