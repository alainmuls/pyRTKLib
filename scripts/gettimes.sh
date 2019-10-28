#! /bin/bash

echo > ./times.txt
for file in `find rtkp/ -name '*.obs' | sort`; do echo ${file} ; TimeRinex ${file} | grep 'obs:' >> ./times.txt ; done