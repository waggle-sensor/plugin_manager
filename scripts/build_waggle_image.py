#!/usr/bin/env python
import time, os, commands, subprocess, shutil
from subprocess import call, check_call
import os.path


data_directory="/root"

report_file="/root/report.txt"


base_images= {'odroid-xu3' : "ubuntu-14.04lts-server-odroid-xu3-20150725.img"}



'''
Will throw exception on execution error.
'''
def run_command(cmd):
    print "execute: %s" % (cmd) 
    try:
        check_call(cmd, shell=True)
    except CalledProcessError as e:
        print "Commmand exited with return code other than zero: %s" % (str(e)) 
        sys.exit(1)
        

def get_output(cmd):
    print "execute: %s" % (cmd) 
    return subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).communicate()[0]


def write_file(filename, content):
    with open(filename, "w") as text_file:
        text_file.write(content)
            

run_command('umount /mnt/newimage/proc /mnt/newimage/dev /mnt/newimage/sys /mnt/newimage/')
stime.sleep(1)
run_command('losetup -d /dev/loop1')
run_command('losetup -d /dev/loop0')



print "usage: ./build_waggle_image.sh 2>&1 | tee build.log"

if not os.path.isfile('waggle_first_boot.sh') :
    print "waggle_first_boot.sh not found. Execute script from script location."
    sys.exit(1)
    

#SCRIPT_data_directory=os.getcwd()


if not call('hash partprobe &> /dev/null'):
    run_command('apt-get install -y parted')


odroid_model_raw=get_output("head -n 1 /media/boot/boot.ini | cut -d '-' -f 1 | tr -d '\n'")
odroid_model=""
if odroid_model_raw == "ODROIDXU":
    print "Detected device: %s" % (odroid_model_raw)
    if not os.path.isfile('/media/boot/exynos5422-odroidxu3.dtb'):
        odroid_model="odroid-xu3"
    else:
        odroid_model="odroid-xu"
        print "Did not find the XU3/4-specific file /media/boot/exynos5422-odroidxu3.dtb."
        sys.exit(1)

elif odroid_model_raw  == "ODROIDC":
    print "Detected device: %s" % (odroid_model)
    odroid_model="odroid-c1"
else:
    print "Could not detect ODROID model. (%s)" % (odroid_model)
    sys.exit(1)





date_today=get_output('date +"%Y%m%d"') 
new_image_prefix="%s/waggle-guestnode-%s-%s" % (data_directory, odroid_model, date_today) 
new_image="%s.img" % (new_image_prefix)

new_image_b="%s_B.img" % (new_image_prefix)


os.chdir(data_directory)

try:
    base_image = base_images[odroid_model]
except:
    print "image %s not found" % (odroid_model)
    sys.exit(1)

base_image_xz = base_image + '.xz'

if not os.path.isfile(base_image_xz):
    run_command('wget http://www.mcs.anl.gov/research/projects/waggle/downloads/'+ base_image_xz)
  

if not os.path.isfile(base_image):
    run_command('unxz --keep '+base_image_xz)
    

os.remove(new_image)

shutil.copyfile(base_image, new_image)



# get partition start position
#fdisk -lu ${base_image}
start_block=int(get_output("fdisk -lu {0} | grep '{0}2' | awk '{print $2}'".format(new_image))

START_POS=start_block*512  #get_output('echo "%s*512" | bc' % (start_block)) 


# create loop device for disk and for root partition
run_command('losetup /dev/loop0 ' + new_image)
run_command('losetup -o %s /dev/loop1 /dev/loop0' % (str(START_POS)))


mount_point="/mnt/newimage/"

os.mkdir(mount_point)

run_command('mount /dev/loop1 %s' % (mount_point))
run_command('mount -o bind /proc %s/proc' % (mount_point))
run_command('mount -o bind /dev  %s/dev' % (mount_point))
run_command('mount -o bind /sys  %s/sys' % (mount_point))



###                              ###
###  Script for chroot execution ###
###                              ###
#${mount_point}/root/build_gn_image.sh
build_guestnode_image='''\
#!/bin/bash
set -x
set -e

###locale
locale-gen "en_US.UTF-8"
dpkg-reconfigure locales

### timezone 
echo "Etc/UTC" > /etc/timezone 
dpkg-reconfigure --frontend noninteractive tzdata

apt-get update
#apt-get upgrade -y
apt-get --no-install-recommends install -y network-manager
apt-get autoclean
apt-get autoremove -y

apt-get install -y git

mkdir -p /usr/lib/waggle/
cd /usr/lib/waggle/
git clone --recursive https://github.com/waggle-sensor/guestnodes.git





### create report
echo "image created: " > {0}
date >> {0}
echo "" >> {0}
uname -a >> {0}
echo "" >> {0}
cat /etc/os-release >> {0}
dpkg -l >> {0}


### mark image for first boot 
touch /root/first_boot

ln -s /usr/lib/waggle/guestnodes/scripts/waggle_first_boot.sh /etc/init.d/waggle_first_boot.sh

#chown root:root /etc/init.d/waggle_first_boot.sh
update-rc.d waggle_first_boot.sh defaults

rm -f /etc/network/interfaces.d/*
rm -f /etc/udev/rules.d/70-persistent-net.rules 


'''.format(report_file)



run_command('chmod +x %s/root/build_gn_image.sh' % (mount_point))

#
# CHROOT HERE
#

run_command('chroot %s /bin/bash /root/build_gn_image.sh' % (mount_point))

# 
# After changeroot
#

os.remove(report_file)
shutil.copyfile(mount_point+report_file, new_image+'.report.txt')



#set static IP
guest_node_etc_network_interfaces_d = '''\
# interfaces(5) file used by ifup(8) and ifdown(8)
# Include files from /etc/network/interfaces.d:
source-directory /etc/network/interfaces.d

auto lo eth0
iface lo inet loopback

iface eth0 inet static
      address 10.31.81.51
      netmask 255.255.255.0
      #gateway 10.31.81.10

'''

write_file(mount_point+'/etc/network/interfaces', guest_node_etc_network_interfaces_d)







old_partition_size_kb=int(get_output('df -BK --output=size /dev/loop1 | tail -n 1 | grep -o "[0-9]\+"'))

run_command('umount /mnt/newimage/{proc,dev,sys,}')



estimated_fs_size_blocks=int(get_output('resize2fs -P /dev/loop1 | grep -o "[0-9]*"') )

block_size=int(get_output('blockdev --getbsz /dev/loop1'))

estimated_fs_size_kb = estimated_fs_size_blocks*block_size/1024


# add 500MB
new_partition_size_kb = estimated_fs_size_kb + (1024*500)


# add 100MB
new_fs_size_kb = estimated_fs_size_kb + (1024*100)

# verify partition:
run_command('e2fsck -f -y /dev/loop1')



sector_size=int(run_command('fdisk -lu {0} | grep "Sector size" | grep -o ": [0-9]*" | grep -o "[0-9]*"'.format(new_image)))


front_size_kb = sector_size * start_block/ 1024

if new_partition_size_kb < old_partition_size_kb: 

    print "new_partition_size_kb is smaller than old_partition_size_kb"

    # shrink filesystem (that does not shrink the partition!)
    run_command('resize2fs -p /dev/loop1 %sK' % (new_fs_size_kb))


    run_command('partprobe  /dev/loop1')

    time.sleep(3)

    ### fdisk (shrink partition)
    # fdisk: (d)elete partition 2 ; (c)reate new partiton 2 ; specify start posirion and size of new partiton
  
    run_command('echo -e "d\n2\nn\np\n2\n%d\n+%dK\nw\n" | fdisk %s' % (start_block, new_partition_size_kb, new_image))
  


    run_command('partprobe /dev/loop1')

    #set +e
    #resize2fs /dev/loop1
    #set -e

    # does not show the new size
    #fdisk -lu ${new_image}

    # shows the new size (-b for bytes)
    #partx --show /dev/loop1 (fails)

    time.sleep(3)

    run_command('e2fsck -n -f /dev/loop1')

    #e2fsck_ok=1
    #set +e
    #while [ ${e2fsck_ok} != "0" ] ; do
    #  e2fsck -f /dev/loop1
    #  e2fsck_ok=$?
    #  sleep 2
    #done
    #set -e

else:
    print "new_partition_size_kb is NOT smaller than old_partition_size_kb"



run_command('losetup -d /dev/loop1')
run_command('losetup -d /dev/loop0')



# add size of boot partition

combined_size_kb = new_partition_size_kb+front_size_kb
combined_size_bytes = (new_partition_size_kb + front_size_kb) * 1024

# from kb to mb
blocks_to_write = combined_size_kb/1024



run_command('pv -per --width 80 --size %d -f %s | dd bs=1M iflag=fullblock count=%d | xz -1 --stdout - > %s.xz_part' % (combined_size_bytes, new_image, blocks_to_write, new_image))


os.rename(new_image+'.xz_part',  new_image+'.xz')




if os.path.isfile( data_directory+ '/waggle-id_rsa'):
    scp_target = 'waggle@terra.mcs.anl.gov:/mcs/www.mcs.anl.gov/research/projects/waggle/downloads/unstable'
    run_command('md5sum $(basename {0}.xz) > {0}.xz.md5sum'.format(new_image) ) 
    run_command('scp -o "StrictHostKeyChecking no" -v -i {0}/waggle-id_rsa {1}.xz {1}.xz.md5sum {2}'.format(data_directory, new_image, scp_target))
  
    if os.path.isfile( new_image_b+'.xz'):
        # upload second image with different UUID's
        run_command( 'md5sum $(basename {0}.xz) > {0}.xz.md5sum'.format(new_image_b))
        run_command('scp -o "StrictHostKeyChecking no" -v -i {0}/waggle-id_rsa {1}.xz {1}.xz.md5sum {2}'.format(data_directory, new_image_b, scp_target))

  
    if os.path.isfile( new_image+'.report.txt'): 
        run_command('scp -o "StrictHostKeyChecking no" -v -i {0}/waggle-id_rsa {1}.report.txt {2}'.format(data_directory, new_image,scp_target))
      
  
    if os.path.isfile( new_image+'.build_log.txt'): 
        run_command('scp -o "StrictHostKeyChecking no" -v -i {0}/waggle-id_rsa {1}.build_log.txt {2}'.format(data_directory, new_image,scp_target))
      
  

