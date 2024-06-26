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

# default is "with_dep"
forest grow clone_tag_if --verbose --tag-override $TEST_DIR/recipes/tag_overrides.yaml
cd src/clone_tag_if
[ "$(git rev-parse --abbrev-ref HEAD)" == "ros_pkg" ]
cd ../.. && rm -rf src/clone_tag_if

# with mode_a
forest grow clone_tag_if --verbose --mode mode_a --tag-override $TEST_DIR/recipes/tag_overrides.yaml
cd src/clone_tag_if
[ "$(git rev-parse --abbrev-ref HEAD)" == "ros_pkg" ]
cd ../.. && rm -rf src/clone_tag_if

# with mode_b
forest grow clone_tag_if --verbose --mode mode_b --tag-override $TEST_DIR/recipes/tag_overrides.yaml
cd src/clone_tag_if
[ "$(git rev-parse --abbrev-ref HEAD)" == "ros_pkg" ]
cd ../.. && rm -rf src/clone_tag_if

SUCCESS=1