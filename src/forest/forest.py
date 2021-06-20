#!/usr/bin/env python3

import argparse
import os

from forest.common.install import install_package

# just a try-except wrapper to catch ctrl+c
def main():
    try:
        return do_main()
    except KeyboardInterrupt:
        print('\nfailed (interrupted by user)')
        return False

# actual main
def do_main():

    # parse cmd line args
    parser = argparse.ArgumentParser(description='forest automatizes cloning and building of software packages')
    parser.add_argument('recipe', help='name of recipe with fetch and build information')
    parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print additional information')
    args = parser.parse_args()

    # verbose mode will show output of any called process
    if args.verbose:
        from common import proc_utils
        proc_utils.call_process_verbose = True

    # define directories for source, build, install
    rootdir = os.getcwd()
    buildroot = os.path.join(rootdir, 'build')
    installdir = os.path.join(rootdir, 'install')
    srcroot = os.path.join(rootdir, 'src')
    buildtype = 'Release'

    # create directories
    for dir in (buildroot, installdir, srcroot):
        if not os.path.exists(dir):
            os.mkdir(dir)

    # perform required installation
    success = install_package(pkg=args.recipe, 
        srcroot=srcroot, 
        buildroot=buildroot,
        installdir=installdir,
        buildtype=buildtype)

    return success


if __name__ == '__main__':
    # return value
    exit(0 if main() else 1)