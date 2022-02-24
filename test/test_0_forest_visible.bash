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

# initialize workspace
forest init

# check expected files and folders do exist
if [ ! -f $WORK_DIR/setup.bash ]; then exit 1; fi
if [ ! -d $WORK_DIR/src ]; then exit 1; fi
if [ ! -d $WORK_DIR/build ]; then exit 1; fi
if [ ! -d $WORK_DIR/install ]; then exit 1; fi
if [ ! -d $WORK_DIR/recipes ]; then exit 1; fi

SUCCESS=1