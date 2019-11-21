#!/usr/bin/env bash

STDOY=105
ENDOY=107
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
NICE='/usr/bin/nice -n 19'

# pythonscripts
PYSBFDAILY=${PYHOMEDIR}/pySBFDaily.py
PYCONVBIN=${PYHOMEDIR}/pyconvbin.py
PYFTPOSNAV=${PYHOMEDIR}/pyftposnav.py
PYRTKPROC=${PYHOMEDIR}/pyrtkproc.py
PYRTKPLOT=${PYHOMEDIR}/pyrtkplot.py
PYPOS2MAVG=${PYHOMEDIR}/pos2movavg.py


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

	DIRRAW=${RXTURP}/${RXTYPE}/${YYDOY}
	DIRRIN=${RXTURP}/${RXTYPE}/rinex/${YYDOY}
	DIRIGS=${RXTURP}/${RXTYPE}/igs/

	printf '\nCreating daily file for '${YYDOY}'\n'
	cd ${DIRRAW}
	${NICE} ${PYSBFDAILY} --dir=${DIRRAW}

	printf '\nDownloading OS files for '${YYDOY}'\n'
	${NICE} ${PYFTPOSNAV} --rootdir=${DIRIGS} --year=20${YY} --doy=${DOY}

	printf '\nCreating RINEX files for '${YYDOY}'\n'
	if [ ${RXTYPE} = 'ASTX' ]
	then
		cd ${DIRRAW}

		MARKER=SEPT

		# the gnss and corresponding marker name lists
		gnss=([0]='gal' [1]='gps' [2]='com')
		gnssmark=([0]='GALI' [1]='GPSS' [2]='COMB')

		for i in "${!gnss[@]}"
		do
			${NICE} ${PYCONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ --rinexdir=${DIRRIN} --rinexver=R3 --binary=SBF --gnss=${gnss[i]} -n ${gnssmark[i]} ${DOY} ${YY}
		done
	elif [ ${RXTYPE} = 'BEGP' ]
	then
		MARKER=BEGP
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
printf '\n'
if [ ${CURBRANCH} != 'master' ]
then
	${GIT} checkout ${CURBRANCH}
fi
