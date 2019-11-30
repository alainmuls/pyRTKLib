#/usr/env/bin bash

usage()
{
    echo "usage: $0 -v pyenv -s startDOY -e endDOY -y YYYY -r RxType [-h]"
}

if [ $# -ne 10 ]; then
    usage
    exit 1
fi

while [ $# -gt 0 ];
do
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

#source the common shell script
source ${HOME}/amPython/${PYVENV}/scripts/common.sh
# ${PYSBFDAILY} -h

for curDOY in $(seq $STDOY $ENDOY)
do
	DOY=$(leading_zero ${curDOY})
	YY=${YYYY: -2}
	YYDOY=${YY}${DOY}
	# printf ${YY}' '${DOY}' '${YYDOY}

	DIRRAW=${RXTURPROOT}/${RXTYPE}/${YYDOY}
	DIRRIN=${RXTURPROOT}/${RXTYPE}/rinex/${YYDOY}
	DIRIGS=${RXTURPROOT}/${RXTYPE}/igs/

	cd ${DIRRAW}

	printf '\nCreating RINEX files for '${YYDOY}'\n'
	if [ ${RXTYPE} = 'ASTX' ]
	then
		MARKER=SEPT

		for i in "${!gnss[@]}"
		do
			${NICE} ${PYCONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ \
				--rinexdir=${DIRRIN} --rinexver=R3 --binary=SBF --gnss=${gnss[i]} \
				-n ${gnssMarker[i]} ${DOY} ${YY}
		done
	else
		MARKER=BEGP

		${NICE} ${PYCONVBIN} --dir=${DIRRAW} --file=${MARKER}${DOY}0.${YY}_ \
			--rinexdir=${DIRRIN} --rinexver=R3 --binary=SBF --gnss=gal \
			-n BEGP ${DOY} ${YY}

		# check existence of OBS file
		BEGPOBS=${DIRRIN}'/BEGP'${DOY}'0.'${YY}'O'
		BEGPNAV=${DIRRIN}'/BEGP'${DOY}'0.'${YY}'E'
		echo ${BEGPOBS}

		# correct in observation file the PRNs for E33 (from E28) and E36 (from E29)
		OLDPRN33='E28'
		OLDPRN36='E29'
		NEWPRN33='E33'
		NEWPRN36='E36'

		${SED} -i "s/${OLDPRN33}/${NEWPRN33}/g" ${BEGPOBS}
		${SED} -i "s/${OLDPRN36}/${NEWPRN36}/g" ${BEGPOBS}
		${SED} -i "s/${OLDPRN33}/${NEWPRN33}/g" ${BEGPNAV}
		${SED} -i "s/${OLDPRN36}/${NEWPRN36}/g" ${BEGPNAV}
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup