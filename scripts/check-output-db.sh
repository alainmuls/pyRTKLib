#!/bin/bash

usage()
{
    echo "usage: $0  -g GNSS -y YYYY -m MARKER [-h]"
}

if [ $# -ne 6 ]; then
    usage
    exit 1
fi

while [ $# -gt 0 ];
do
    case $1 in
		-g)	shift
        	GNSS=$1 ;;
        -m) shift
			MARKER=$1 ;;
    	-y) shift
			YYYY=$1 ;;
        *)  usage
            exit 1
    esac
    	shift
done

echo ${GNSS}
echo ${MARKER}
echo ${YYYY}

AWK=/usr/bin/awk
GREP=/usr/bin/grep
WC=/usr/bin/wc
DBOUT=/home/amuls/RxTURP/glab_output_db.csv

count=`${AWK} -F "," '{print $1","$2","$3","$4}' ${DBOUT} | ${GREP} "${GNSS},${MARKER}" | sort | uniq | ${GREP} ^${YYYY} | ${WC} -l`

echo "Found "${count}" fields for "${GNSS}"/"${MARKER}" in "${DBOUT}