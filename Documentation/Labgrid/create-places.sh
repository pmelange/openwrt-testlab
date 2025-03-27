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
		labgrid-client -p port$i add-match $(hostname)/testdev$j/RemoteNetworkInterface
		labgrid-client -p port$i add-match $(hostname)/testdev$j/NetworkService
		labgrid-client -p port$i add-match $(hostname)/testdev$j/RemoteTFTPProvider
	fi
	
done

echo creating aux1
labgrid-client -p aux1 create
labgrid-client -p aux1 add-match $(hostname)/aux1/NetworkSysfsGPIO
echo creating aux2
labgrid-client -p aux2 create
labgrid-client -p aux2 add-match $(hostname)/aux2/NetworkSysfsGPIO
