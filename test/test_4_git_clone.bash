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
forest grow git_clone_sha1 --verbose

cd src/git_clone_sha1
[ "$(git log --pretty=format:'%h' -n 1)" == "da69af6" ]

SUCCESS=1