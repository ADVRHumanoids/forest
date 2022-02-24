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
cp $TEST_DIR/recipes/*.yaml recipes 
sudo apt remove -y sl || true
! dpkg -s sl
forest grow sl_from_apt --verbose
dpkg -s sl 

SUCCESS=1