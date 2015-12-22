#!/bin/bash
set -x
set -e

export DIR="/root"

if [ $# -eq 0 ] ; then
  echo "usage: $0 <device>"
  echo ""
  echo "list of available devices: (do not specify partitions!)"
  blkid
  exit 1
fi


cd /root

export IMAGE="ubuntu-14.04lts-server-odroid-xu3-20150725.img"
if [ ! -e ${IMAGE}.xz ] ; then
  wget http://www.mcs.anl.gov/research/projects/waggle/downloads/${IMAGE}.xz
  unxz --keep ${IMAGE}.xz
fi

# get partition start position
#fdisk -lu ${IMAGE}
export START_BLOCK=$(fdisk -lu ${IMAGE} | grep "${IMAGE}2" | grep -o " [0-9]\+ \+[0-9]\+ \+[0-9]\+ \+83" | cut -d ' ' -f 2) ; echo "START_BLOCK: ${START_BLOCK}"

export START_POS=$(echo "${START_BLOCK}*512" | bc) ; echo "START_POS: ${START_POS}"

# create loop device
losetup -o ${START_POS} /dev/loop0 ${IMAGE}


export IMAGEDIR="/mnt/newimage/"

mkdir -p ${IMAGEDIR}
mount /dev/loop0 ${IMAGEDIR}
mount -o bind /proc ${IMAGEDIR}/proc
mount -o bind /dev ${IMAGEDIR}/dev
mount -o bind /sys ${IMAGEDIR}/sys


###                              ###
###  Script for chroot execution ###
###                              ###

cat <<EOF > ${IMAGEDIR}/root/build_gn_image.sh
#!/bin/bash

###locale
locale-gen "en_US.UTF-8"
dpkg-reconfigure locales

### timezone 
echo "Etc/UTC" > /etc/timezone 
dpkg-reconfigure --frontend noninteractive tzdata

apt-get update
apt-get upgrade -y
apt-get --no-install-recommends install -y network-manager
apt-get autoclean
apt-get autoremove -y


### mark image for first boot 
touch /root/first_boot


rm -f /etc/network/interfaces.d/*
rm -f /etc/udev/rules.d/70-persistent-net.rules 


EOF

chmod +x ${IMAGEDIR}/root/build_gn_image.sh

chroot ${IMAGEDIR} /bin/bash /root/build_gn_image.sh

# After changeroot
#set static IP
cat <<EOF >  ${IMAGEDIR}/etc/network/interfaces
# interfaces(5) file used by ifup(8) and ifdown(8)
# Include files from /etc/network/interfaces.d:
source-directory /etc/network/interfaces.d

auto lo eth0
iface lo inet loopback

iface eth0 inet static
      address 10.31.81.51
      netmask 255.255.255.0
      #gateway 10.31.81.10

EOF



umount /mnt/newimage/proc
umount /mnt/newimage/dev
umount /mnt/newimage/sys
umount /mnt/newimage
losetup -d /dev/loop0





