#! /bin/bash

echo -n > ./times.txt
for file in `find ./ -name '*.19O' | sort`; do
	echo 'Extracting times from '${file}
	TimeRinex ${file} | grep '19O:' >> ./times.txt
done
