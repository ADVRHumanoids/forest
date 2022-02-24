#!/bin/bash

TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $TEST_DIR

# exit on error
set -o xtrace
set -e 
SUCCESS=0

# test 1
source $TEST_DIR/common.bash
cd $WORK_DIR
pwd 

forest init
source setup.bash
cp $TEST_DIR/recipes/*.yaml recipes 
forest grow forest_test --verbose
if [ ! -f $WORK_DIR/install/share/forest_test/a_file.txt ]; then exit 1; fi
if [ -f $WORK_DIR/install/share/forest_test/b_file.txt ]; then exit 1; fi

# test 2
source $TEST_DIR/common.bash
cd $WORK_DIR
pwd 

forest init
source setup.bash
cp $TEST_DIR/recipes/*.yaml recipes 
forest grow forest_test -m opt_b --verbose
if [ ! -f $WORK_DIR/install/share/forest_test/a_file.txt ]; then exit 1; fi
if [ ! -f $WORK_DIR/install/share/forest_test/b_file.txt ]; then exit 1; fi


SUCCESS=1