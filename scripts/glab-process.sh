#/usr/env/bin bash

usage()
{
    echo "usage: $0 -v pyenv -b git-branch -s startDOY -e endDOY -y YYYY -r RxType  [-h]"
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
    DIRGLAB=${DIRRIN}/glab
    DIRIGS=${RXTURPROOT}/igs/

    # echo 'DIRRX = '${DIRRX}
    # echo 'DIRRAW = '${DIRRAW}
    # echo 'DIRRIN = '${DIRRIN}
    # echo 'DIRIGS = '${DIRIGS}

    echo 'Processing receiver '${RXTYPE}
    if [ ${RXTYPE} = 'ASTX' ]
    then
        MARKER=COMB
        echo ${MARKER}
        GNSSS=('E' 'G' 'EG')
        for GNSS in ${GNSSS[*]}
        do
            echo ${GNSS}

            if [ ${GNSS} = 'G' ]
            then
                GPSCODES=('C1C' 'C1W' 'C2L' 'C2W' 'C2W' 'C5Q')
                for GPSCODE in ${GPSCODES[*]}
                do
                    echo 'GPSCODE = '${GPSCODE}
                    ${NICE} ${GLABPROC} -y ${YYYY} -d ${curDOY} -r ${RXTYPE} -g ${GNSS} -m ${MARKER} -p ${GPSCODE}
                    ${NICE} ${GLABMSGOUTPUT} -r ${DIRGLAB} -s 5 -f ${MARKER}-${GNSS}-${GPSCODE}.out.gz
                done
            elif [ ${GNSS} = 'E' ]
            then
                GALCODES=('C1C' 'C5Q')
                for GALCODE in ${GALCODES[*]}
                do
                    echo 'GALCODE = '${GALCODE}
                    ${NICE} ${GLABPROC} -y ${YYYY} -d ${curDOY} -r ${RXTYPE} -g ${GNSS} -m ${MARKER} -p ${GALCODE}
                    ${NICE} ${GLABMSGOUTPUT} -r ${DIRGLAB} -s 5 -f ${MARKER}-${GNSS}-${GALCODE}.out.gz
                done
            elif [ ${GNSS} = 'EG' ]
            then
                GNSSCODES=('C1C' 'C5Q')
                USEGNSS='E G'
                for GNSSCODE in ${GNSSCODES[*]}
                do
                    echo 'GNSSCODE = '${GNSSCODE}
                    ${NICE} ${GLABPROC} -y ${YYYY} -d ${curDOY} -r ${RXTYPE} -g ${USEGNSS} -m ${MARKER} -p ${GNSSCODE}
                    ${NICE} ${GLABMSGOUTPUT} -r ${DIRGLAB} -s 5 -f ${MARKER}-${GNSS}-${GNSSCODE}.out.gz
                done
            fi
        done
    elif [ ${RXTYPE} = 'BEGP' ]
        then
            MARKER='GPRS'
            GNSS='E'
            PRSCODES=('C1A' 'C6A')
            for PRSCODE in ${PRSCODES[*]}
            do
                echo 'PRSCODE = '${PRSCODE}
                ${NICE} ${GLABPROC} -y ${YYYY} -d ${curDOY} -r ${RXTYPE} -g ${GNSS} -m ${MARKER} -p ${PRSCODE}
                ${NICE} ${GLABMSGOUTPUT} -r ${DIRGLAB} -s 5 -f ${MARKER}-${GNSS}-${PRSCODE}.out.gz
            done
        fi

done


# glab_processing.py -y ${YYYY} -d ${DOY} -r ASTX -g G -m COMB -p C1C;


# frequency 1:  G01-32                                       C1W C1C | L1C     | D1C
# frequency 1:  E01-36                                       C1C     | L1C     | D1C
# frequency 2:  G01 G03-10 G12 G15 G17 G24-27 G29-32         C2W C2L | L2W L2L | D2W D2L
# frequency 2:  G02 G11 G13-14 G16 G18-23 G28                C2W     | L2W     | D2W
# frequency 5:  G01 G03-04 G06 G08-10 G24-27 G30 G32 E01-36  C5Q     | L5Q     | D5Q
