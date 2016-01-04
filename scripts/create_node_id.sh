#!/bin/bash

set -e


if [ -e /media/boot/boot.ini ] ; then
  export ODROIDMODEL=`head -n 1 /media/boot/boot.ini | cut -d '-' -f 1`

fi

echo "ODROIDMODEL: $ODROIDMODEL"

if [ $(echo $ODROIDMODEL | grep "^ODROID" | wc -l) -eq 0 ] ; then
  echo "warning: could not detect ODROID model"
fi

### Node ID
export NODE_ID=""


#IS_ODROIDC=$(echo $ODROIDMODEL | grep "^ODROIDC" | wc -l)



# try MAC address (some older models do not have unique MAC addresses)


# try to detect network device, e.g. "eth0"
export NETWORK_DEVICE=$(ifconfig -a | grep "Ethernet" | grep "^eth" | sort | head -n 1 | grep -o "^eth[0-9]" | tr -d '\n')
echo "NETWORK_DEVICE: ${NETWORK_DEVICE}"
export MACADDRESS=`ifconfig ${NETWORK_DEVICE} | head -n 1 | grep -o "[[:xdigit:]:]\{17\}" | sed 's/://g'`
echo "MACADDRESS: ${MACADDRESS}"
if [ ! ${#MACADDRESS} -ge 12 ]; then
  echo "warning: could not extract MAC address"
else
  NODE_ID="0000${MACADDRESS}"  
fi

# try memory card serial number
export CID_FILE="/sys/block/mmcblk0/device/cid"
if [ "${NODE_ID}x" == "x" ] && [ -e ${CID_FILE} ]; then
  echo "try using serial number from SD-card"
  # some devices do not have a unique MAC address, they could use this code
 
  export SERIAL_ID=`python -c "cid = '$(cat ${CID_FILE})' ; len=len(cid) ; mid=cid[:2] ; psn=cid[-14:-6] ; print mid+psn"`
  if [ ! ${#SERIAL_ID} -ge 11 ]; then
    echo "warning: could not create unique identifier from SD-card serial number"
  else
    NODE_ID="000000${SERIAL_ID}" 
  fi
fi


echo "NODE_ID: ${NODE_ID}"

# try random number
if [ "${NODE_ID}x" = "x" ] ; then
  NODE_ID=`openssl rand -hex 8`
fi

echo "NODE_ID: ${NODE_ID}"

if [ "${NODE_ID}x" = "x" ] ; then
  echo "could not generate NODE_ID"
  exit 1
fi

#save node ID
mkdir -p /etc/waggle/
echo ${NODE_ID} > /etc/waggle/node_id

