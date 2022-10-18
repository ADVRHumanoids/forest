#!/bin/bash

if [ -z "$ROS_DISTRO" ]; 
then echo "ROS is not installed, exiting"; exit 0 
else echo "ROS $ROS_DISTRO detected"; 
fi


TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $TEST_DIR

# exit on error
set -exo
SUCCESS=0

# test 1
source $TEST_DIR/common.bash
cd $WORK_DIR
 

forest init
source setup.bash
cp -r $TEST_DIR/recipes recipes
forest grow ros_pkg --verbose

tree || true
if [ ! -f $WORK_DIR/ros_src/ros_pkg/CMakeLists.txt ]; then exit 1; fi
if [ ! -f $WORK_DIR/ros_src/ros_pkg/package.xml ]; then exit 1; fi

if [[ ! "$(rospack find forest_test)" == "$WORK_DIR/ros_src/ros_pkg" ]]; then exit 1; fi

SUCCESS=1