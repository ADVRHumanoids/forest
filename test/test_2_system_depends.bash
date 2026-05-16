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
sudo apt remove -y sl cowsay || true
python -m pip uninstall -y meme || true
! python -m pip show meme
! dpkg -s sl
! dpkg -s cowsay
forest grow pkg_with_system_deps --verbose
dpkg -s sl 
dpkg -s cowsay
python -m pip show meme

SUCCESS=1