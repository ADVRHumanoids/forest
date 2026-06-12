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

# suffix-based .lock mapping file
cp $TEST_DIR/recipes/tag_overrides.yaml tag_overrides.lock
forest grow clone_tag_if --verbose --tag-override tag_overrides.lock
cd src/clone_tag_if
[ "$(git rev-parse --abbrev-ref HEAD)" == "ros_pkg" ]
cd ../.. && rm -rf src/clone_tag_if

# json mapping file
echo '{"clone_tag_if": "ros_pkg"}' > tag_overrides.json
forest grow clone_tag_if --verbose --tag-override tag_overrides.json
cd src/clone_tag_if
[ "$(git rev-parse --abbrev-ref HEAD)" == "ros_pkg" ]
cd ../.. && rm -rf src/clone_tag_if

# single scalar tag override for one recipe
forest grow clone_tag_if --verbose --tag-override ros_pkg
cd src/clone_tag_if
[ "$(git rev-parse --abbrev-ref HEAD)" == "ros_pkg" ]
cd ../.. && rm -rf src/clone_tag_if

# multiple inline pkg:=tag overrides
forest grow clone_tag_if ros_pkg --src-only --verbose --tag-override clone_tag_if:=ros_pkg ros_pkg:=ros_pkg
cd src/clone_tag_if
[ "$(git rev-parse --abbrev-ref HEAD)" == "ros_pkg" ]
cd ../.. && rm -rf src/clone_tag_if src/ros_pkg ros_src/ros_pkg

# scalar override is rejected for multiple recipes
if forest grow clone_tag_if ros_pkg --src-only --tag-override ros_pkg; then
    echo "scalar override with multiple recipes should have failed"
    exit 1
fi

# a single pkg:=tag value is interpreted as a scalar tag, not an inline mapping
forest grow empty --src-only --tag-override empty:=ros_pkg

# malformed multi-value inline overrides are rejected
if forest grow clone_tag_if --tag-override clone_tag_if:=ros_pkg malformed; then
    echo "malformed multi-value override should have failed"
    exit 1
fi

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
