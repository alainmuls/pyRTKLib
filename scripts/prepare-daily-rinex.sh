#/usr/env/bin bash

usage()
{
    echo "usage: $0 -v pyenv -b git-bracnh -s startDOY -e endDOY -y YYYY -r RxType [-h]"
}

if [ $# -ne 12 ]; then
    usage
    exit 1
fi

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
	DIRRAW=${DIRRX}/${YYDOY}
	DIRRIN=${DIRRX}/rinex/${YYDOY}
	DIRIGS=${DIRRX}/igs/

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
		printf '\nCreating RINEX files for '${RXTYPE}' @ '${YYDOY}'\n'

		if [ ${RXTYPE} = 'ASTX' ]
		then
			MARKER=SEPT

			# for i in "${!gnss[@]}"
			# do
			${NICE} ${PYCONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ \
				--rinexdir=${DIRRIN} --binary=SBF
			# done

		elif [ ${RXTYPE} = 'BEGP' ]
		then
			MARKER=BEGP

			${NICE} ${PYCONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ \
				--rinexdir=${DIRRIN} --binary=SBF

			# # check existence of OBS file
			# BEGPOBS=${DIRRIN}'/BEGP'${DOY}'0.'${YY}'O'
			# BEGPNAV=${DIRRIN}'/BEGP'${DOY}'0.'${YY}'E'
			# echo ${BEGPOBS}

			# # correct in observation file the PRNs for E33 (from E28) and E36 (from E29)
			# OLDPRN33='E28'
			# OLDPRN36='E29'
			# NEWPRN33='E33'
			# NEWPRN36='E36'

			# ${SED} -i "s/${OLDPRN33}/${NEWPRN33}/g" ${BEGPOBS}
			# ${SED} -i "s/${OLDPRN36}/${NEWPRN36}/g" ${BEGPOBS}
			# ${SED} -i "s/${OLDPRN33}/${NEWPRN33}/g" ${BEGPNAV}
			# ${SED} -i "s/${OLDPRN36}/${NEWPRN36}/g" ${BEGPNAV}
		fi
	else
		echo 'No raw data available for '${RXTYPE}' @ '${YY}' '${DOY}
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup