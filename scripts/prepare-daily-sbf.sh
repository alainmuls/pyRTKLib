#!/bin/bash

usage()
{
    echo "usage: $0 -v pyenv-s startDOY -e endDOY -y YYYY -r RxType [-h]"
}

if [ $# -ne 10	 ]; then
    usage
    exit 1
fi

while [ $# -gt 0 ]
do
    case $1 in
		-v)	shift
        	PYVENV=$1
            ;;
		-s)	shift
        	STDOY=$1
            ;;
        -e) shift
			ENDOY=$1
            ;;
    	-y) shift
			YYYY=$1
            ;;
        -r) shift
			RXTYPE=$1
			;;
        *)  usage
            exit 1
    esac
    	shift
done

echo ${PYVENV}
echo ${STDOY}
echo ${ENDOY}
echo ${YYYY}
echo ${RXTYPE}

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

for curDOY in $(seq $STDOY $ENDOY)
do
	DOY=$(leading_zero ${curDOY})
	YY=${YYYY: -2}
	YYDOY=${YY}${DOY}
	# printf ${YY}' '${DOY}' '${YYDOY}

	DIRRAW=${RXTURP}/${RXTYPE}/${YYDOY}
	DIRRIN=${RXTURP}/${RXTYPE}/rinex/${YYDOY}
	DIRIGS=${RXTURP}/${RXTYPE}/igs/

	printf '\nCreating daily file for '${YYDOY}'\n'
	cd ${DIRRAW}
	${NICE} ${PYSBFDAILY} --dir=${DIRRAW} --overwrite
	exit_status=$?
	if [ $exit_status -eq 0 ]
	then
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
		fi
		for i in "${!gnss[@]}"
		do
			${NICE} ${PYCONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ --rinexdir=${DIRRIN} --rinexver=R3 --binary=SBF --gnss=${gnss[i]} -n ${gnssmark[i]} ${DOY} ${YY}
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
