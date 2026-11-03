#!/bin/bash
set -e
TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python3 "$TEST_DIR/test_versioned_depends.py"
