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

	DIRIGS=${RXTURPROOT}/${RXTYPE}/igs/
	cd ${DIRIGS}

	printf '\nDownloading OS files for '${YYDOY}'\n'
	${NICE} ${PYFTPOSNAV} --rootdir=${DIRIGS} --year=20${YY} --doy=${DOY}
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
cleanup
