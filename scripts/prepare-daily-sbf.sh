#!/bin/bash

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

	# create logging infor for current GNSS raw data
	gnss_log_msg=${RXTYPE}','${YY}','${DOY}','${YYDOY}','${DIRRAW}
	# echo 'gnss_log_msg = '${gnss_log_msg}

	printf '\nCreating daily SBF file for '${YYDOY}'\n'
	# echo ${NICE} ${PYSBFDAILY} --dir=${DIRRAW}  # --overwrite
	${NICE} ${PYSBFDAILY} --dir=${DIRRAW}  # --overwrite
	rc=$?

	# examine return code to determine whether data is present
	if [[ ${rc} == 0 ]]
	then
		gnss_log_msg_bool=',true'
	else
		gnss_log_msg_bool=',false'
	fi
	# echo ${gnss_log_msg}${gnss_log_msg_bool}

	# add/replace information within the GNSSRAWDATA file
	if [[ -f ${GNSSRAWDATA} ]]
	then
		if ${GREP} --quiet ${gnss_log_msg} ${GNSSRAWDATA}
		then
			${SED} --quiet "s|^${gnss_log_msg}*|${gnss_log_msg}${gnss_log_msg_bool}|g" ${GNSSRAWDATA}
			# echo change_line ${gnss_log_msg} ${gnss_log_msg}${gnss_log_msg_bool} ${GNSSRAWDATA}
			change_line ${gnss_log_msg} ${gnss_log_msg}${gnss_log_msg_bool} ${GNSSRAWDATA}
		else
			echo ${gnss_log_msg}${gnss_log_msg_bool} >> ${GNSSRAWDATA}
		fi
	else
		echo ${gnss_log_msg}${gnss_log_msg_bool} > ${GNSSRAWDATA}
	fi

done

# sort the file based on first 3 fields
temp_file=$(mktemp)
${SORT} --key=1,3 ${GNSSRAWDATA} > ${temp_file}
${CP} ${temp_file} ${GNSSRAWDATA}
${RM} ${temp_file}

# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup
