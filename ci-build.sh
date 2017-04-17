#!/bin/bash -xe

python3 --version
python3 -mpycodestyle --version

# Target directory for all build files
BUILD=${1:-ci-build}
rm -rf ${BUILD}/
mkdir -p $BUILD

python3 -mpycodestyle --ignore E501,E741,E305,E722,E402 tests zenpy

# Check that the setup.py script works
rm -rf ${BUILD}/test-install ${BUILD}/test-install-bin
mkdir ${BUILD}/test-install ${BUILD}/test-install-bin
PYTHONPATH=${BUILD}/test-install python3 setup.py --quiet install --install-lib ${BUILD}/test-install --install-scripts ${BUILD}/test-install-bin

#test -f ${BUILD}/test-install-bin/zenpy

PYTHONPATH=${BUILD}/test-install python3 -m unittest discover -s tests
