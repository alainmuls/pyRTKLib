#!/bin/bash

usage()
{
    echo "usage: $0 -v pyenv -b git-branch -s startDOY -e endDOY -y YYYY -r RxType [-h]"
}

# number of arguments
argc=$#

if [[ $argc -eq 12 ]]; then
	while [[ $# -gt 0 ]]; do
	    case $1 in
			-v)	shift
	        	PYVENV=$1 ;;
        -b) shift
			BRANCH=$1;;
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
	DIRIGS=${RXTURPROOT}/igs/${YYDOY}

	PROCESSINGFILE=${RXTURPROOT}/${RXTYPE}/rtkprocessing.txt
	${TOUCH} ${PROCESSINGFILE}

	echo 'DIRRIN = '${DIRRIN}
	echo 'DIRIGS = '${DIRIGS}

	cd ${DIRRIN}

	if [[ ${RXTYPE} = 'ASTX' ]]; then
		for i in "${!gnss[@]}"; do
			echo '\n'${i}': '${gnss[i]}

			gnsslower=${gnss[i],,}
			gnss=${gnsslower:0:3}
			# find out which RINEX Obs files are available
			ROVEROBSFILES=`ls -1 ${gnssMarker[i]}*${YY}D.Z`

			# find out which RINEX Nav files are available
			ROVERNAV=`ls -1 ${gnssMarker[i]}*${YY}${gnssNavExt[i]}.Z`
			# create names for igs downloaded nav file
			IGSNAV=${igsNavName[i]}00${igsNavCountry[i]}_R_${YYYY}${DOY}0000_01D_${igsNavNameExt[i]}N.rnx.gz

			# process each OBS file
			echo -n /tmp/proc.t
			for ROVEROBS in ${ROVEROBSFILES}
			do
				echo '... ROVEROBS='${ROVEROBS}
				echo '... Processing '${gnssMarker[i]}' '${YY}' '${DOY}': '${ROVEROBS}' '${ROVERNAV}' '${IGSNAV}' '${DIRRIN}
				echo ${gnssMarker[i]}' '${YY}' '${DOY}': '${ROVEROBS}' '${ROVERNAV}' '${IGSNAV}' '${DIRRIN} >> ${PROCESSINGFILE}
				echo ${PYRTKPROC} --dir=${DIRRIN} --rover=${ROVEROBS} --freq=4 --cutoff=5 -e ${ROVERNAV} ${DIRIGS}/${IGSNAV} --gnss=${gnss} >> /tmp/proc.t
				${NICE} ${PYRTKPROC} --dir=${DIRRIN} --rover=${ROVEROBS} --freq=4 --cutoff=5 -e ${ROVERNAV} ${DIRIGS}/${IGSNAV} --gnss=${gnss}

			done

			# # cp the log file to the directory where the processing placed its files
			# # ${CP} ${LOGPYRTKPROC} ${DIRRIN}/'pyrtkproc-'${gnssMarker[i]}'-'${YY}'-'${DOY}'.log'
		done
	elif [[ ${RXTYPE} = 'TURP' ]]; then
		# find out which combinations of RINEX Obs/Nav files are available
		ls -1 ${DIRRIN}/*.Z

		# # create names for obs / nav file of rover station
		# ROVEROBS='TURP'${DOY}'0.'${YY}'O'
		# ROVERNAV='TURP'${DOY}'0.'${YY}'E'

		# # create names for igs downloaded nav file
		# IGSNAV=${igsNavName[0]}00${igsNavCountry[0]}_R_${YYYY}${DOY}0000_01D_${igsNavNameExt[0]}N.rnx.gz

		# echo 'Processing: '${RXTYPE}' '${YY}' '${DOY}': '${ROVEROBS}' '${ROVERNAV}' '${IGSNAV}' '${DIRRIN} >> ${PROCESSINGFILE}
		# ${NICE} ${PYRTKPROC} --dir=${DIRRIN} --rover=${ROVEROBS} --freq=4 --cutoff=5 -e ${ROVERNAV} ${DIRIGS}/${IGSNAV} --gnss=gal

		# # cp the log file to the directory where the processing placed its files
		# # ${CP} ${LOGPYRTKPROC} ${DIRRIN}/'pyrtkproc-TURP-'${YY}'-'${DOY}'.log'
	fi
done


# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup
