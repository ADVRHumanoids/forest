#!/bin/bash

TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $TEST_DIR

# exit on error
set -e 
SUCCESS=0

# test 1
source $TEST_DIR/common.bash
cd $WORK_DIR
pwd 

forest init
source setup.bash
cp -r $TEST_DIR/recipes recipes
forest grow custom_build --verbose -j 2

if [ ! -f $WORK_DIR/src/custom_build/a_file_2.txt ]; then exit 1; fi
if [ ! -f $WORK_DIR/install/share/custom_build/b_file.txt ]; then exit 1; fi

SUCCESS=1