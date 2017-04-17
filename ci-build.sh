#!/bin/bash -xe

python --version
python -mpycodestyle --version

# Target directory for all build files
BUILD=${1:-ci-build}
rm -rf ${BUILD}/
mkdir -p $BUILD

python -mpycodestyle --ignore E501,E741,E305,E722,E402 tests zenpy

# Check that the setup.py script works
rm -rf ${BUILD}/test-install ${BUILD}/test-install-bin
mkdir ${BUILD}/test-install ${BUILD}/test-install-bin
PYTHONPATH=${BUILD}/test-install python setup.py --quiet install --install-lib ${BUILD}/test-install --install-scripts ${BUILD}/test-install-bin

#test -f ${BUILD}/test-install-bin/zenpy

python -m unittest discover -s tests

