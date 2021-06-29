#!/usr/bin/env python3

import argparse
import os
import sys
import argcomplete

from forest.common.install import install_package, write_setup_file
from forest.common.package import Package

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
    parser.add_argument('recipe', nargs='?', choices=Package.get_available_recipes(), help='name of recipe with fetch and build information')
    parser.add_argument('--list', '-l', required=False, action='store_true', help='list available recipes')
    parser.add_argument('--jobs', '-j', default=1, help='parallel jobs for building')
    parser.add_argument('--init', '-i', required=False, action='store_true', help='initialize the workspace only')
    parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print additional information')
    buildtypes = ['None', 'RelWithDebInfo', 'Release', 'Debug']
    parser.add_argument('--build-type', '-t', default=buildtypes[1], choices=buildtypes, help='build type for cmake')

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if not args.init and not args.list and args.recipe is None:
        print('positional argument "recipe" is required unless --init or --list is passed', file=sys.stderr)
        return False

    # verbose mode will show output of any called process
    if args.verbose:
        from forest.common import proc_utils
        proc_utils.call_process_verbose = True

    # print available packages
    if args.list:
        print(' '.join(Package.get_available_recipes()))
        return True

    # define directories for source, build, install
    rootdir = os.getcwd()
    buildroot = os.path.join(rootdir, 'build')
    installdir = os.path.join(rootdir, 'install')
    srcroot = os.path.join(rootdir, 'src')
    buildtype = args.build_type

    # create directories
    for dir in (buildroot, installdir, srcroot):
        if not os.path.exists(dir):
            os.mkdir(dir)

    # create setup.bash if does not exist
    write_setup_file(installdir=installdir)

    # if init mode, stop here
    if args.init:
        return True

    # perform required installation
    success = install_package(pkg=args.recipe, 
        srcroot=srcroot, 
        buildroot=buildroot,
        installdir=installdir,
        buildtype=buildtype,
        jobs=args.jobs)

    return success


if __name__ == '__main__':
    # return value
    exit(0 if main() else 1)