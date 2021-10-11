#!/usr/bin/env python3

import argparse
import os
import sys
import argcomplete
from datetime import datetime

from forest.common.install import install_package, write_setup_file, write_ws_file, check_ws_file
from forest.common.package import Package
from forest.common import recipe

# just a try-except wrapper to catch ctrl+c
def main():
    try:
        if not do_main():
            print('(failed)')
            sys.exit(1)
        sys.exit(0)
    except KeyboardInterrupt:
        print('\nfailed (interrupted by user)')
        sys.exit(1)

# actual main
def do_main():

    # define directories for source, build, install, and recipes
    rootdir = os.getcwd()
    recipesdir = os.path.join(rootdir, 'recipes')
    buildroot = os.path.join(rootdir, 'build')
    installdir = os.path.join(rootdir, 'install')
    srcroot = os.path.join(rootdir, 'src')

    # create recipes file
    recipe.CookBook.set_recipe_fname(rootdir, recipe_fname='recipes.yaml')
    
    # set recipe dir
    Package.set_recipe_path(recipesdir)

    # available recipes
    available_recipes = Package.get_available_recipes()
    if len(available_recipes) == 0:
        available_recipes = None

    # parse cmd line args
    buildtypes = ['None', 'RelWithDebInfo', 'Release', 'Debug']
    cloneprotos = ['ssh', 'https']
    dfl_log_file = datetime.now().strftime("/tmp/forest_%Y_%m_%d_%H_%M_%S.log")

    parser = argparse.ArgumentParser(description='forest automatizes cloning and building of software packages')
    parser.add_argument('--init', '-i', required=False, action='store_true', help='initialize the workspace only')
    parser.add_argument('recipe', nargs='?', choices=available_recipes, help='name of recipe with fetch and build information')
    parser.add_argument('--add-recipes', '-a', nargs=2,  metavar=('URL', 'TAG'), required=False, help='fetch recipes from git repository; two arguments are required, i.e., <url> <tag> (e.g. git@github.com:<username>/<reponame>.git master or https://github.com/<username>/<reponame>.git master')
    parser.add_argument('--update', '-u', required=False, action='store_true', help='update recipes')
    parser.add_argument('--jobs', '-j', default=1, help='parallel jobs for building')
    parser.add_argument('--list', '-l', required=False, action='store_true', help='list available recipes')
    parser.add_argument('--mode', '-m', nargs='+', required=False, help='specify modes that are used to set conditional compilation flags (e.g., cmake args)')
    parser.add_argument('--config', '-c', nargs='+', required=False, help='specify configuration variables that can be used inside recipes')
    parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print additional information')
    parser.add_argument('--default-build-type', '-t', default=buildtypes[1], choices=buildtypes, help='build type for cmake, it is overridden by recipe')
    parser.add_argument('--force-reconfigure', required=False, action='store_true', help='force calling cmake before building with args from the recipe')
    parser.add_argument('--list-eval-locals', required=False, action='store_true', help='print available attributes when using conditional build args')
    parser.add_argument('--clone-protocol', required=False, choices=cloneprotos, help='override clone protocol')
    parser.add_argument('--log-file', default=dfl_log_file, help='log file for non-verbose mode')

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # verbose mode will show output of any called process
    if args.verbose:
        from forest.common import proc_utils
        proc_utils.call_process_verbose = True

    if not args.verbose:
        from forest.common import print_utils
        print_utils.log_file = open(args.log_file, 'w')

    # print available packages
    if args.list:
        print(' '.join(Package.get_available_recipes()))
        return True

    # set config vars
    if args.config:
        from forest.common import config_handler
        ch = config_handler.ConfigHandler.instance()
        ch.set_config_variables(args.config)

    # print available local attributes for conditional args
    if args.list_eval_locals:
        from forest.common import eval_handler
        eval_handler.EvalHandler.print_available_locals()
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
        print('adding recipes...')
        if not recipe.CookBook.add_recipes(entries=args.add_recipes):
            return False

    # if required, update recipes
    if args.update:
        print('updating recipes...')
        if not recipe.CookBook.update_recipes():
            return False

    # clone proto
    if args.clone_protocol is not None:
        from forest.common.fetch_handler import GitFetcher
        GitFetcher.proto_override = args.clone_protocol

    # no recipe to install, exit
    if args.recipe is None:
        print('no recipe to build, exiting...')
        return True

    # handle modes
    if args.mode is not None:
        Package.modes = set(args.mode)

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
    main()