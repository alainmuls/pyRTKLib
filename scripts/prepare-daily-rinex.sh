#/usr/env/bin bash

usage()
{
    echo "usage: $0 -v pyenv -b git-branch -s startDOY -e endDOY -y YYYY -r RxType [-h]"
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
	# echo 'GNSSRAWDATA = '${GNSSRAWDATA}

	# check whether a raw daily GNSS file is present to convert to RINEX
	# echo ${GREP} "${gnss_log_msg}" ${GNSSRAWDATA}
	${GREP} "${gnss_log_msg}" ${GNSSRAWDATA} | ${GREP} true
	rc=$?
	# echo "rc = "${rc}

	# process if return code is 0
	if [[ ${rc} == 0 ]]
	then
		gnss_log_msg=${gnss_log_msg}',true'

		printf '\nCreating RINEX files for '${RXTYPE}' @ '${YYDOY}'\n'

		# add info about processing to the ${GNSSRAWDATA} file
		info_txt=${RXTYPE}','${YY}','${DOY}','${YYDOY}','${DIRRAW}',true'  # OLD text
		new_info_txt=${info_txt}  # NEW text

		if [ ${RXTYPE} = 'ASTX' ]
		then
			MARKER=SEPT

			# echo ${NICE} ${GFZRNX_CONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ --rinexdir=${DIRRIN} --binary=SBF

			${NICE} ${GFZRNX_CONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ \
				--rinexdir=${DIRRIN} --binary=SBF

			for i in "${!gnss[@]}"
			do
				obs_name=${gnssMarker[i]}${DOY}'0.'${YY}'D.Z'
				if [[ -f ${DIRRIN}'/'${obs_name} ]]
				then
					nav_name=${gnssMarker[i]}${DOY}0.${YY}${gnssNavExt[i]}'.gz'
					obs_size=`${DU} -h ${DIRRIN}/${obs_name} | ${CUT} -f1`
					nav_size=`${DU} -h ${DIRRIN}/${nav_name} | ${CUT} -f1`
					new_info_txt=${new_info_txt}','${obs_name}','${obs_size}','${nav_name}','${nav_size}
					# echo ${i}' => '${new_info_txt}
				fi
			done
			# echo 'info_txt = '${info_txt}
			# echo 'new_info_txt = '${new_info_txt}

			# change_line "TEXT_TO_BE_REPLACED" "This line is removed by the admin." yourFile
			change_line ${info_txt} ${new_info_txt} ${GNSSRAWDATA}

		elif [ ${RXTYPE} = 'BEGP' ]
		then
			MARKER=BEGP

			# echo ${NICE} ${GFZRNX_CONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ --rinexdir=${DIRRIN} --binary=SBF

			${NICE} ${GFZRNX_CONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ \
				--rinexdir=${DIRRIN} --binary=SBF

			# check whether RINEX obs/nav files are created and put in ${GNSSRAWDATA}
			obs_name='GPRS'${DOY}0.${YY}'D.Z'

			if [[ -f ${DIRRIN}'/'${obs_name} ]]
			then
				nav_name='GPRS'${DOY}0.${YY}'P.gz'
				obs_size=`${DU} -h ${DIRRIN}/${obs_name} | ${CUT} -f1`
				nav_size=`${DU} -h ${DIRRIN}/${nav_name} | ${CUT} -f1`
				new_info_txt=${new_info_txt}','${obs_name}','${obs_size}','${nav_name}','${nav_size}
			fi
			# echo 'info_txt = '${info_txt}
			# echo 'new_info_txt = '${new_info_txt}

			# change_line "TEXT_TO_BE_REPLACED" "This line is removed by the admin." yourFile
			change_line ${info_txt} ${new_info_txt} ${GNSSRAWDATA}

			# # check existence of OBS file
			# BEGPOBS=${DIRRIN}'/TURP'${DOY}'0.'${YY}'O'
			# BEGPNAV=${DIRRIN}'/TURP'${DOY}'0.'${YY}'E'
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
		echo 'No RINEX data available for '${RXTYPE}' @ '${YY}' '${DOY}
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup