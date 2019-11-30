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

	DIRRIN=${RXTURP}/${RXTYPE}/rinex/${YYDOY}
	DIRIGS=${RXTURP}/${RXTYPE}/igs/${YYDOY}

	PROCESSINGFILE=${RXTURP}/${RXTYPE}/rtkprocessing.txt
	${TOUCH} ${PROCESSINGFILE}

	echo 'DIRRIN = '${DIRRIN}
	echo 'DIRIGS = '${DIRIGS}

	if [[ ${RXTYPE} = 'ASTX' ]]; then
		for i in "${!gnss[@]}"; do
			# create names for obs / nav file of rover station
			ROVEROBS=${gnssMarker[i]}${DOY}'0.'${YY}O
			ROVERNAV=${gnssMarker[i]}${DOY}'0.'${YY}${gnssNavExt[i]}

			# create names for igs downloaded nav file
			IGSNAV=${igsNavName[i]}00${igsNavCountry[i]}_R_${YYYY}${DOY}0000_01D_${igsNavNameExt[i]}N.rnx.gz

			echo 'Processing: '${gnss[i]}' '${YY}' '${DOY}': '${ROVEROBS}' '${ROVERNAV}' '${IGSNAV}' '${DIRRIN} >> ${PROCESSINGFILE}
			${NICE} ${PYRTKPROC} --dir=${DIRRIN} --rover=${ROVEROBS} --freq=4 --cutoff=5 -e ${ROVERNAV} ${DIRIGS}/${IGSNAV} --gnss=${gnss[i]}
		done
	elif [[ ${RXTYPE} = 'BEGP' ]]; then
		# create names for obs / nav file of rover station
		ROVEROBS='BEGP'${DOY}'0.'${YY}O
		ROVERNAV='BEGP'${DOY}'0.'${YY}E


		# create names for igs downloaded nav file
		IGSNAV=${igsNavName[0]}00${igsNavCountry[0]}_R_${YYYY}${DOY}0000_01D_${igsNavNameExt[0]}N.rnx.gz

		echo 'Processing: '${RXTYPE}' '${YY}' '${DOY}': '${ROVEROBS}' '${ROVERNAV}' '${IGSNAV}' '${DIRRIN} >> ${PROCESSINGFILE}
		${NICE} ${PYRTKPROC} --dir=${DIRRIN} --rover=${ROVEROBS} --freq=4 --cutoff=5 -e ${ROVERNAV} ${DIRIGS}/${IGSNAV} --gnss=gal
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
printf '\n'
if [[ ${CURBRANCH} != 'master' ]]; then
	${GIT} checkout ${CURBRANCH}
fi

