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

# clone two packages (source only, no build needed)
forest grow git_clone_sha1 --src-only --verbose
forest grow ros_pkg --src-only --verbose

# --- test 1: basic freeze ---
forest freeze
[ -f forest.lock ]

SHA1_GIT_CLONE=$(cd src/git_clone_sha1 && git rev-parse HEAD)
SHA1_ROS_PKG=$(cd src/ros_pkg && git rev-parse HEAD)

grep -q "git_clone_sha1: ${SHA1_GIT_CLONE}" forest.lock
grep -q "ros_pkg: ${SHA1_ROS_PKG}" forest.lock

echo "test 1 passed: forest.lock created with correct sha1s"

# --- test 2: freeze fails on dirty repo ---
echo "dirty" >> src/git_clone_sha1/README.md
if forest freeze 2>/dev/null; then
    echo "test 2 FAILED: should have failed on dirty repo"
    exit 1
fi
git -C src/git_clone_sha1 checkout -- . && git -C src/git_clone_sha1 clean -fd
echo "test 2 passed: freeze correctly rejected dirty repo"

# --- test 3: --ignore-errors on dirty repo still produces lock ---
echo "dirty" >> src/git_clone_sha1/README.md
forest freeze --ignore-errors
grep -q "ros_pkg: ${SHA1_ROS_PKG}" forest.lock
if grep -q "git_clone_sha1:" forest.lock; then
    echo "test 3 FAILED: dirty repo should be absent from lock"
    exit 1
fi
git -C src/git_clone_sha1 checkout -- . && git -C src/git_clone_sha1 clean -fd
echo "test 3 passed: --ignore-errors skipped dirty repo and wrote lock"

# --- test 4: freeze fails on non-git directory ---
mkdir src/not_a_repo
if forest freeze 2>/dev/null; then
    echo "test 4 FAILED: should have failed on non-git directory"
    exit 1
fi
rmdir src/not_a_repo
echo "test 4 passed: freeze correctly rejected non-git directory"

# --- test 5: --append merges without clobbering existing entries ---
# Write a fake entry for a package not in src
echo "phantom_pkg: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" > forest.lock
forest freeze --append
grep -q "phantom_pkg: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" forest.lock
grep -q "git_clone_sha1: ${SHA1_GIT_CLONE}" forest.lock
grep -q "ros_pkg: ${SHA1_ROS_PKG}" forest.lock
echo "test 5 passed: --append preserved existing entries"

# --- test 6: freeze + grow --tag-override reproduces exact commits ---
# Freeze current state (ros_pkg is on its branch tip)
forest freeze

# Patch the lock to pin ros_pkg to the first commit (da69af6 - known to exist in this repo)
PINNED_SHA1="da69af6fe4b8c9101505adbbb4087f926c2edd9d"
python3 -c "
import yaml
with open('forest.lock') as f:
    lock = yaml.safe_load(f)
lock['ros_pkg'] = '${PINNED_SHA1}'
with open('forest.lock', 'w') as f:
    yaml.dump(lock, f, default_flow_style=False)
"

# Remove and re-clone using the patched lock as tag override
rm -rf src/ros_pkg ros_src/ros_pkg
forest grow ros_pkg --src-only --tag-override forest.lock --verbose

RESTORED_SHA1=$(cd src/ros_pkg && git rev-parse HEAD)
[ "$RESTORED_SHA1" == "$PINNED_SHA1" ]
echo "test 6 passed: grow --tag-override used pinned sha1 from lock"

SUCCESS=1
