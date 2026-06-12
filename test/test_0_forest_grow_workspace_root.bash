#!/bin/bash

TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $TEST_DIR

# exit on error
set -e
SUCCESS=0

source $TEST_DIR/common.bash
cd $WORK_DIR

forest init
source setup.bash
cp -r $TEST_DIR/recipes recipes

mkdir -p src/custom_fetch src/empty src/missing_recipe

OUTPUT=$(forest grow --src-only 2>&1)
echo "$OUTPUT"
[[ "$OUTPUT" == *"[forest] warning: package missing_recipe has no available recipe, skipping"* ]]
[[ "$OUTPUT" == *"[forest] building custom_fetch empty with 1 parallel job"* ]]

OUTPUT=$(forest grow --src-only --blacklist custom_fetch 2>&1)
echo "$OUTPUT"
[[ "$OUTPUT" == *"[forest] warning: package missing_recipe has no available recipe, skipping"* ]]
[[ "$OUTPUT" == *"[forest] building empty with 1 parallel job"* ]]
[[ "$OUTPUT" != *"building custom_fetch"* ]]

SUCCESS=1
