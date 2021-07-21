#!/usr/bin/env python3

import argparse
import os
import sys
import argcomplete

from forest.common.install import install_package, write_setup_file, write_ws_file, check_ws_file
from forest.common.package import Package
from forest.common import recipe

# just a try-except wrapper to catch ctrl+c
def main():
    try:
        return do_main()
    except KeyboardInterrupt:
        print('\nfailed (interrupted by user)')
        return False

# actual main
def do_main():

    # define directories for source, build, install, and recipes
    rootdir = os.getcwd()
    recipesdir = os.path.join(rootdir, 'recipes')
    buildroot = os.path.join(rootdir, 'build')
    installdir = os.path.join(rootdir, 'install')
    srcroot = os.path.join(rootdir, 'src')

    # create recipes file
    recipe.write_recipes_yaml_file(rootdir=rootdir)
    
    # set recipe dir
    Package.set_recipe_path(recipesdir)

    # available recipes
    available_recipes = Package.get_available_recipes()
    if len(available_recipes) == 0:
        available_recipes = None

    # parse cmd line args
    parser = argparse.ArgumentParser(description='forest automatizes cloning and building of software packages')
    parser.add_argument('--init', '-i', required=False, action='store_true', help='initialize the workspace only')
    parser.add_argument('recipe', nargs='?', choices=available_recipes, help='name of recipe with fetch and build information')
    parser.add_argument('--add-recipes', '-a', nargs=2,  metavar=('URL', 'TAG'), required=False, help='fetch recipes from git repository; two arguments are required, i.e., <url> <tag> (e.g. git@github.com:<username>/<reponame>.git master or https://github.com/<username>/<reponame>.git master')
    parser.add_argument('--update', '-u', required=False, action='store_true', help='update recipes')
    parser.add_argument('--jobs', '-j', default=1, help='parallel jobs for building')
    parser.add_argument('--mode', '-m', nargs='+', required=False, help='specify modes that are used to set conditional compilation flags (e.g., cmake args)')
    parser.add_argument('--list', '-l', required=False, action='store_true', help='list available recipes')
    parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print additional information')
    buildtypes = ['None', 'RelWithDebInfo', 'Release', 'Debug']
    parser.add_argument('--default-build-type', '-t', default=buildtypes[1], choices=buildtypes, help='build type for cmake, it is overridden by recipe')
    parser.add_argument('--force-reconfigure', required=False, action='store_true', help='force calling cmake before building with args from the recipe')

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

    # initialize workspace
    if args.init:
        # create directories
        for dir in (buildroot, installdir, srcroot, recipesdir):
            if not os.path.exists(dir):
                os.mkdir(dir)

        # create setup.bash if does not exist
        write_setup_file(installdir=installdir)

        # create marker file
        write_ws_file(rootdir=rootdir)  # note: error on failure?

        return True

    # check ws
    if not check_ws_file(rootdir=rootdir):
        print(f'current directory {rootdir} is not a forest workspace.. \
have you called forest --init ?', file=sys.stderr)
        return False

    # if required, add a recipe repository to the list of remotes
    if args.add_recipes is not None:
        if not recipe.add_recipe_repository(entries=args.add_recipes):
            return False


    # if required, update recipes
    if args.update:
        return recipe.fetch_recipes_from_file(os.path.join(rootdir, 'recipes.yaml'))

    # no recipe to install, exit
    if args.recipe is None:
        print('no recipe to build, exiting..')
        return True

    # handle modes
    if args.mode is not None:
        Package.modes = args.modes

    # print jobs
    print(f'building {args.recipe} with {args.jobs} parallel job{"s" if int(args.jobs) > 1 else ""}')

    # perform required installation
    success = install_package(pkg=args.recipe,
                                srcroot=srcroot,
                                buildroot=buildroot,
                                installdir=installdir,
                                buildtype=args.default_build_type,
                                jobs=args.jobs,
                                reconfigure=args.force_reconfigure
                                )

    return success


if __name__ == '__main__':
    # return value
    exit(0 if main() else 1)