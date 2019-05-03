#!/bin/bash

SETUP_INI_PATH=./Setup.ini
UPMU_ADDRESS="172.16.1.101"
FTP_CONFIG_PASSWORD=/wagglerw/waggle/upmu_ftp_password

password=$(cat ${FTP_CONFIG_PASSWORD})

echo "## Sending" ${SETUP_INI_PATH} " to uPMU " ${UPMU_ADDRESS} " ##"

code=$(curl -s -w "%{http_code}\n" -T ${SETUP_INI_PATH} ftp://ftp_config:${password}@${UPMU_ADDRESS})
echo "## Operation done with http code: " ${code} " ##"
echo "## Please allow at least 5 minutes for the device to reset ##"