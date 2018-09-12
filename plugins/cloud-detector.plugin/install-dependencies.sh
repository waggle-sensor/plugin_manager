#!/bin/sh

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
