#/usr/env/bin bash

usage()
{
    echo "usage: $0 -v pyenv -b git-branch -s startDOY -e endDOY -y YYYY -r RxType [-h]"
}

if [ $# -ne 12 ]; then
    usage
    exit 1
firm

while [ $# -gt 0 ];
do
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

#source the common shell script
source ${HOME}/amPython/${PYVENV}/scripts/common.sh
# ${PYSBFDAILY} -h

for curDOY in $(seq $STDOY $ENDOY)
do
	DOY=$(leading_zero ${curDOY})
	YY=${YYYY: -2}
	YYDOY=${YY}${DOY}
	# printf ${YY}' '${DOY}' '${YYDOY}

	DIRRX=${RXTURPROOT}/${RXTYPE}
	DIRYYDOY=${DIRRX}/rinex/${YYDOY}/
	# echo 'DIRRX = '${DIRRX}
	# echo 'DIRRAW = '${DIRRAW}
	# echo 'DIRRIN = '${DIRRIN}
	# echo 'DIRIGS = '${DIRIGS}

	# create logging info text found in ${GNSSRAWDATA} and check whether we have TRUE or FALSE
	gnss_log_msg=${RXTYPE}','${YY}','${DOY}','${YYDOY}','${DIRRAW}
	# echo 'gnss_log_msg = '${gnss_log_msg}

	# check whether a raw daily GNSS file is present to convert to RINEX
	${GREP} "${gnss_log_msg}" ${GNSSRAWDATA} | ${GREP} true
	rc=$?
	# echo ${rc}

	# process if return code is 0
	if [[ ${rc} == 0 ]]
	then
		gnss_log_msg=${gnss_log_msg}',true'


		# add info about processing to the ${GNSSRAWDATA} file
		info_txt=${RXTYPE}','${YY}','${DOY}','${YYDOY}','${DIRRAW}',true'  # OLD text
		new_info_txt=${info_txt}  # NEW text

		if [ ${RXTYPE} = 'ASTX' ]
		then
			# process the GALI and GPSN obstab
			for satsyst in E G
			do
				printf '\nProcessing observation statistics for '${RXTYPE}'/'${satsyst}' @ '${YYDOY}'\n'
				${RNX_OBS_TABULAR} -d ${DIRYYDOY} -g ${satsyst} -m 30
			done
		elif [ ${RXTYPE} = 'TURP' ]
		then
			# process the GALI and GPSN obstab
			for satsyst in E
			do
				printf '\nProcessing observation statistics for '${RXTYPE}'/'${satsyst}' @ '${YYDOY}'\n'
				${RNX_OBS_TABULAR} -d ${DIRYYDOY} -g ${satsyst} -m 30
			done
		fi
	else
		echo 'No RINEX data available for '${RXTYPE}' @ '${YY}' '${DOY}
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup