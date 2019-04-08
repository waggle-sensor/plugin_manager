#!/bin/sh
# ANL:waggle-license
#  This file is part of the Waggle Platform.  Please see the file
#  LICENSE.waggle.txt for the legal details of the copyright and software
#  license.  For more details on the Waggle project, visit:
#           http://www.wa8.gl
# ANL:waggle-license

set -e

cleanup() {
	waggle-switch-to-operation-mode
}

trap cleanup EXIT

waggle-switch-to-safe-mode

apt-get install \
  build-essential \
  cython3 \
  python3-matplotlib \
  python3-numpy \
  python3-pil \
  python3-scipy \
  python3-skimage
