#!/bin/bash

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

	DIRRX=${RXTURPROOT}/${RXTYPE}
	DIRRAW=${DIRRX}/${YYDOY}
	DIRRIN=${DIRRX}/rinex/${YYDOY}
	DIRIGS=${DIRRX}/igs/

	echo 'DIRRX = '${DIRRX}
	echo 'DIRRAW = '${DIRRAW}
	echo 'DIRRIN = '${DIRRIN}
	echo 'DIRIGS = '${DIRIGS}

	# file with directories containing Raw SBF data
	DIRSRAWSBF=${DIRRX}/dirs_sbf.t
	DIRSNOSBF=${DIRRX}/dirs_no_sbf.t

	printf '\nCreating daily SBF file for '${YYDOY}'\n'
	if [ -d ${DIRRAW} ]
	then
		echo ${DIRRAW} >> ${DIRSRAWSBF}
		cd ${DIRRAW}

		${NICE} ${PYSBFDAILY} --dir=${DIRRAW}  # --overwrite
	else
		echo ${DIRRAW} >> ${DIRSNOSBF}
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup
