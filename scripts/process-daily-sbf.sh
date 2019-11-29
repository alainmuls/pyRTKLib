#!/bin/bash

usage()
{
    echo "usage: $0 -v pyenv -s startDOY -e endDOY -y YYYY -r RxType [-g GNSS] [-h]"
}

argc=$#
echo $argc
if [ $argc -eq 12 ] || [ $argc -gt 10 ]
then
    usage
    exit 1
fi

while [ $# -gt 0 ];
do
	echo $1
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
		-g) shift
			GNSS=$1 ;;
        *)  usage
            exit 1
    esac
    	shift
done

echo ${PYVENV}
echo ${STDOY}
echo ${ENDOY}
echo ${YYYY}
echo ${RXTYPE}

#source the common shell script
source ${HOME}/amPython/${PYVENV}/scripts/common.sh
# ${PYRTKPROC} -h


for curDOY in $(seq $STDOY $ENDOY)
do
	DOY=$(leading_zero ${curDOY})
	YY=${YYYY: -2}
	YYDOY=${YY}${DOY}
	# printf ${YY}' '${DOY}' '${YYDOY}

	DIRRIN=${RXTURP}/${RXTYPE}/rinex/${YYDOY}
	DIRIGS=${RXTURP}/${RXTYPE}/igs/${YYDOY}

	echo 'DIRRIN = '${DIRRIN}
	echo 'DIRIGS = '${DIRIGS}

	if [ ${RXTYPE} = 'ASTX' ]
	then
		for i in "${!gnss[@]}"
		do
			# create names for obs / nav file of rover station
			ROVEROBS=${gnssMarker[i]}${DOY}'0.'${YY}O
			ROVERNAV=${gnssMarker[i]}${DOY}'0.'${YY}${gnssNavExt[i]}

			# create names for igs downloaded nav file
			IGSNAV=${igsNavName[i]}00${igsNavCountry[i]}_R_${YYYY}${DOY}0000_01D_${igsNavNameExt[i]}N.rnx.gz

			echo 'Processing: '${gnss[i]}' -> '${ROVEROBS}' '${ROVERNAV}' '${IGSNAV} >> ${DIRRIN}/rtkprocessing.txt
			${NICE} ${PYRTKPROC} --dir=${DIRRIN} --rover=${ROVEROBS} --freq=4 --cutoff=5 -e ${ROVERNAV} ${DIRIGS}/${IGSNAV} --gnss=${gnss[i]}
		done
	fi
done

# return to git branch we had in original shell
cd ${PYHOMEDIR}
printf '\n'
if [ ${CURBRANCH} != 'master' ]
then
	${GIT} checkout ${CURBRANCH}
fi
