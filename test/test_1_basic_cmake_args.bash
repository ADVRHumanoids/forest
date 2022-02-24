#!/bin/bash

TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $TEST_DIR

# exit on error
set -o xtrace
set -e 
SUCCESS=0

## test 1
source $TEST_DIR/common.bash
cd $WORK_DIR
pwd 

forest init
source setup.bash
cp $TEST_DIR/recipes/*.yaml recipes 
forest grow forest_test --verbose
if [ ! -f $WORK_DIR/install/share/forest_test/a_file.txt ]; then exit 1; fi
if [ -f $WORK_DIR/install/share/forest_test/b_file.txt ]; then exit 1; fi  # b_file not installed by default

# test 2
source $TEST_DIR/common.bash
cd $WORK_DIR
pwd 

forest init
source setup.bash
cp $TEST_DIR/recipes/*.yaml recipes 
forest grow forest_test --cmake-args INSTALL_B_FILE=ON --verbose  # this cmake arg triggers installation of b_file
if [ ! -f $WORK_DIR/install/share/forest_test/a_file.txt ]; then exit 1; fi
if [ ! -f $WORK_DIR/install/share/forest_test/b_file.txt ]; then exit 1; fi  # check b_file exists


SUCCESS=1