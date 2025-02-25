#!/bin/bash

for i in $(seq 1 10); do
	printf -v j "%02d" $i
	labgrid-client -p port$i show  &> /dev/null
	if [ "$?" == "1" ]; then
		echo creating port$i
		labgrid-client -p port$i create
		labgrid-client -p port$i add-named-match $(hostname)/testdev$j/NetworkSysfsGPIO/power power
		labgrid-client -p port$i add-named-match $(hostname)/testdev$j/NetworkSysfsGPIO/reset reset
		labgrid-client -p port$i add-match $(hostname)/testdev$j/NetworkSerialPort
	fi
	
done
