#!/bin/bash

usage()
{
    echo "usage: $0 -v pyenv -s startDOY -e endDOY -y YYYY -r RxType [-h]"
}

# number of arguments
argc=$#

if [[ $argc -eq 10 ]]; then
	while [[ $# -gt 0 ]]; do
	    case $1 in
			-v)	shift
	        	PYVENV=$1 ;;
			-s)	shift
	        	STDOY=$1 ;;
	        -e) shift
				ENDOY=$1 ;;
	    	-y) shift
				YYYY=$1 ;;
	        -r) shift
				RXTYPE=$1 ;;
	        *)  usage
	            exit 1
	    esac
	    	shift
	done
else
    usage
    exit 1
fi

echo 'PYVENV = '${PYVENV}
echo 'STDOY = '${STDOY}
echo 'ENDOY = '${ENDOY}
echo 'YYYY = '${YYYY}
echo 'RXTYPE = '${RXTYPE}

#source the common shell script
source ${HOME}/amPython/${PYVENV}/scripts/common.sh
# ${PYRTKPROC} -h


for curDOY in $(seq $STDOY $ENDOY); do
	DOY=$(leading_zero ${curDOY})
	YY=${YYYY: -2}
	YYDOY=${YY}${DOY}
	# printf ${YY}' '${DOY}' '${YYDOY}

	DIRRIN=${RXTURPROOT}/${RXTYPE}/rinex/${YYDOY}
	DIRIGS=${RXTURPROOT}/${RXTYPE}/igs/${YYDOY}

	PLOTTINGFILE=${RXTURPROOT}/${RXTYPE}/rtkplot.txt
	${TOUCH} ${PLOTTINGFILE}

	echo 'DIRRIN = '${DIRRIN}
	echo 'DIRIGS = '${DIRIGS}

	if [[ ${RXTYPE} = 'ASTX' ]]; then
		for i in "${!gnss[@]}"; do
			# create name for POS file
			ROVERPOS=${gnssMarker[i]}${DOY}'0-'${YY}'O.pos'
			DIRPOS=${DIRRIN}/rtkp/${gnss[i]}

			echo 'Plotting: '${gnssMarker[i]}' '${YY}' '${DOY}': '${ROVERPOS}' '${DIRPOS} >> ${PLOTTINGFILE}
			${NICE} ${PYRTKPLOT} --dir=${DIRPOS} --file=${ROVERPOS}

			# cp the log file to the directory where the processing placed its files
			${CP} ${LOGPYRTKPLOT} ${DIRRIN}/'pyrtkplot-'${gnssMarker[i]}'-'${YY}'-'${DOY}'.log'
		done
	elif [[ ${RXTYPE} = 'TURP' ]]; then
		# create name for POS file
		ROVERPOS='TURP'${DOY}'0-'${YY}'O.pos'
		DIRPOS=${DIRRIN}/rtkp/gal

		echo 'Plotting: '${RXTYPE}' '${YY}' '${DOY}': '${ROVERPOS}' '${DIRPOS} >> ${PLOTTINGFILE}
		${NICE} ${PYRTKPLOT} --dir=${DIRPOS} --file=${ROVERPOS}

		# cp the log file to the directory where the processing placed its files
		${CP} ${LOGPYRTKPLOT} ${DIRRIN}/'pyrtkplot-TURP-'${YY}'-'${DOY}'.log'
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup
