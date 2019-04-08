#!/bin/bash
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license

protobuf=$(protoc --version)

if [[ $protobuf = "libprotoc"* ]]
then
    echo protobuf version: $protobuf is already installed
else
    echo protobuf is installing...

    curl -OL https://github.com/google/protobuf/releases/download/v3.2.0/protoc-3.2.0-linux-x86_64.zip
    unzip protoc-3.2.0-linux-x86_64.zip -d protoc3
    sudo mv protoc3/bin/* /usr/local/bin/
    sudo mv protoc3/include/* /usr/local/include/    

    cd ..
    protoc object_detection/protos/*.proto --python_out=.
    sed -i '$ export PYTHONPATH=$PYTHONPATH:`pwd`:`pwd`/slim' ~/.bashrc
    source ~/.bashrc
    cd LabelImg

    protobuf=$(protoc --version)
    echo protobuf version: $protobuf is installed
fi

pyqt5=$(sudo apt-cache policy pyqt5-dev-tools)

if [[ $pyqt5 = *none* ]]
then
    echo pyqt5 is already installed
else
    echo qt5 is installing..

    sudo apt-get install pyqt5-dev-tools
    pyrcc5 -o resources.py resources.qrc
fi

    echo lxml is installing..
    sudo pip3 install lxml


## Excute labeling program
#python3 labelImg.py
