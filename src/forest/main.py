#!/usr/bin/env python3

import argparse
import os
import sys
import argcomplete

from forest.common.install import install_package, write_setup_file, write_ws_file, check_ws_file, write_recipes_yaml_file
from forest.common.package import Package
from forest.common.recipe import fetch_recipes_from_file

# just a try-except wrapper to catch ctrl+c
def main():
    try:
        return do_main()
    except KeyboardInterrupt:
        print('\nfailed (interrupted by user)')
        return False

# actual main
def do_main():
    rootdir = os.getcwd()
    recipesdir = os.path.join(rootdir, 'recipes')
    Package.set_recipe_path(recipesdir)

    # parse cmd line args
    parser = argparse.ArgumentParser(description='forest automatizes cloning and building of software packages')
    parser.add_argument('recipe', nargs='?', choices=Package.get_available_recipes(), help='name of recipe with fetch and build information')
    parser.add_argument('--list', '-l', required=False, action='store_true', help='list available recipes')
    parser.add_argument('--update', '-u', required=False, action='store_true', help='update recipes')
    parser.add_argument('--jobs', '-j', default=1, help='parallel jobs for building')
    parser.add_argument('--init', '-i', required=False, action='store_true', help='initialize the workspace only')
    parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print additional information')
    buildtypes = ['None', 'RelWithDebInfo', 'Release', 'Debug']
    parser.add_argument('--default-build-type', '-t', default=buildtypes[1], choices=buildtypes, help='build type for cmake, it is overridden by recipe')
    parser.add_argument('--reconfigure', required=False, action='store_true', help='print additional information')

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # verbose mode will show output of any called process
    if args.verbose:
        from forest.common import proc_utils
        proc_utils.call_process_verbose = True

    # print available packages
    if args.list:
        print(' '.join(Package.get_available_recipes()))
        return True

    # define directories for source, build, install, and recipes
    buildroot = os.path.join(rootdir, 'build')
    installdir = os.path.join(rootdir, 'install')
    srcroot = os.path.join(rootdir, 'src')
    buildtype = args.default_build_type

    # initialize workspace
    if args.init:
        # create directories
        for dir in (buildroot, installdir, srcroot):
            if not os.path.exists(dir):
                os.mkdir(dir)

        # create setup.bash if does not exist
        write_setup_file(installdir=installdir)

        # create marker file
        write_ws_file(rootdir=rootdir)  # note: error on failure?

        write_recipes_yaml_file(rootdir=rootdir)

        # make_recipes_dir
        os.mkdir(recipesdir)

    if args.update:
        success = fetch_recipes_from_file(os.path.join(rootdir, 'recipes.yaml'))

    # no recipe to install, exit
    else:
        if args.recipe is None:
            print('no recipe to build, exiting..')
            return True

        # check ws
        if not check_ws_file(rootdir=rootdir):
            print(f'current directory {rootdir} is not a forest workspace.. \
    have you called forest --init ?', file=sys.stderr)
            return False

        # print jobs
        print(f'building {args.recipe} with {args.jobs} parallel jobs')

        # perform required installation
        success = install_package(pkg=args.recipe,
                                  srcroot=srcroot,
                                  buildroot=buildroot,
                                  installdir=installdir,
                                  buildtype=buildtype,
                                  jobs=args.jobs,
                                  reconfigure=args.reconfigure
                                  )

    return success


if __name__ == '__main__':
    # return value
    exit(0 if main() else 1)