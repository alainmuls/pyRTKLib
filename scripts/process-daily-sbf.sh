#!/usr/bin/env bash

STDOY=109
ENDOY=110
YY=19

# print DOY with leading zeros if needed
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
# printf ${VIRTUAL_ENV}

# set the start directory
RXTURP=${HOME}/RxTURP/BEGPIOS
RXTYPE=ASTX

# commands
GIT=/usr/bin/git
GREP=/bin/grep
TR=/usr/bin/tr

# pythonscripts
PYSBFDAILY=${PYHOMEDIR}/pySBFDaily.py
PYCONVBIN=${PYHOMEDIR}/pyconvbin.py
PYFTPOSNAV=${PYHOMEDIR}/pyftposnav.py
PYRTKPROC=${PYHOMEDIR}/pyrtkproc.py
PYRTKPLOT=${PYHOMEDIR}/pyrtkplot.py
POYPOS2MAVG=${PYHOMEDIR}/pos2movavg.py


# make sure to be on the master branch
CURBRANCH=`${GIT} branch | ${GREP} ^* | ${TR} -d '*'`
if [ ${CURBRANCH} != 'master' ]
then
	${GIT} checkout master
fi

source ${VIRTUAL_ENV}/bin/activate
printf '\nActivated python virtual environment '${PROJECT_HOME}/${PROJECT_NAME}'\n'

# ${PYHOMEDIR}/pySBFDaily.py -h

for DOY in $(seq $STDOY $ENDOY)
do
	DOY=$(leading_zero ${DOY})
	YYDOY=${YY}${DOY}
	# printf ${YY}' '${DOY}' '${YYDOY}

	printf '\nCreating daily file for '${YYDOY}'\n'
	cd ${RXTURP}/${RXTYPE}/${YYDOY}
	${PYSBFDAILY} --dir=${RXTURP}/${RXTYPE}/${YYDOY}

	printf '\nCreating RINEX files for '${YYDOY}'\n'
	if [ ${RXTYPE} = 'ASTX' ]
	then
		MARKER=SEPT
		for gnss in gal gps com
		do
			echo ${PYCONVBIN} --dir=${RXTURP}/${RXTYPE}/${YYDOY} --file=${MARKER}${DOY}0.${YY}_ --rinexdir=${RXTURP}/${RXTYPE}/rinex/${YYDOY} --rinexver=R3 --binary=SBF --gnss=${gnss} -n ${gnss} ${DOY} ${YY}
		done
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
printf '\n'
if [ ${CURBRANCH} != 'master' ]
then
	${GIT} checkout ${CURBRANCH}
fi
