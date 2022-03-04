#!/bin/bash

TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $TEST_DIR

# exit on error
set -e 
SUCCESS=0

# test 1
source $TEST_DIR/common.bash
cd $WORK_DIR

# clone recipes (default)
forest init
forest add-recipes git@github.com:advrhumanoids/forest-test.git -t recipes
forest grow my_test_pkg


# test 1
source $TEST_DIR/common.bash
cd $WORK_DIR

# clone recipes (default)
forest init
forest add-recipes git@github.com:advrhumanoids/forest-test.git -t recipes --clone-protocol https -v
forest grow my_test_pkg

SUCCESS=1