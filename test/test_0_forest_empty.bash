#!/bin/bash

TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $TEST_DIR

# exit on error
set -e 
SUCCESS=0

# test 1
source $TEST_DIR/common.bash
cd $WORK_DIR

# initialize workspace
forest --init

# copy recipes
cp $TEST_DIR/recipes/*.yaml recipes 

# check expected files and folders do exist
source setup.bash 

# test empty recipe
forest empty

SUCCESS=1