#!/usr/bin/env python3

import argparse
import getpass
import os
import sys
import argcomplete
from datetime import datetime
from forest import cmake_tools
from forest.common.eval_handler import EvalHandler

from forest.common.install import install_package, write_setup_file, write_ws_file, check_ws_file, uninstall_package, \
    clean
from forest.common.package import Package
from forest.common import recipe
from pprint import pprint

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
    parser.add_argument('--add-recipe-src', '-a', nargs=2,  metavar=('URL', 'TAG'), required=False, help='add recipe source; two arguments are required, i.e., <url> <tag> (e.g. git@github.com:<username>/<reponame>.git master or https://github.com/<username>/<reponame>.git master')
    parser.add_argument('--update-recipes', '-u', nargs='*', choices=available_recipes, required=False, metavar='RECIPE', help='update recipes')
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
    parser.add_argument('--cmake-args', nargs='+', required=False, help='specify additional cmake args to be appended to each recipe (leading -D must be omitted)')
    parser.add_argument('--no-deps', '-n', required=False, action='store_true', help='skip dependency fetch and build step')
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument('--no-pwd', required=False, action='store_true', help='do not prompt for password at the beginning')
    command_group.add_argument('--debug-pwd', default=None, help='')
    parser.add_argument('--uninstall', required=False, action='store_true', help='uninstall recipe')
    parser.add_argument('--clean', required=False, action='store_true', help='uninstall recipe and remove build')

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

        # create marker file
        write_ws_file(rootdir=rootdir)  # note: error on failure?

    # check ws
    if not check_ws_file(rootdir=rootdir):
        print(f'current directory {rootdir} is not a forest workspace.. \
have you called forest --init ?', file=sys.stderr)
        return False

    # create recipes file if doesn't exists
    recipe.CookBook.write_recipe_file(rootdir, recipe_fname='recipes.yaml')

    # create directories
    for dir in (buildroot, installdir, srcroot, recipesdir):
        if not os.path.exists(dir):
            os.mkdir(dir)

    # create setup.bash if does not exist
    write_setup_file(srcdir=srcroot, installdir=installdir)

    # clone proto
    if args.clone_protocol is not None:
        from forest.common.fetch_handler import GitFetcher
        GitFetcher.proto_override = args.clone_protocol


    # if required, add a recipe repository to the list of remotes
    if args.add_recipe_src is not None:
        print('adding recipes...')
        if not recipe.CookBook().add_recipe_src(entry=args.add_recipe_src):
            return False

    # if required, update recipes
    if args.update_recipes is not None:
        # if update args was used
        # see https://stackoverflow.com/questions/30487767/check-if-argparse-optional-argument-is-set-or-not
        print('updating recipes...')
        if not args.update_recipes:
            # empty list -> update all
            if not recipe.CookBook().update_recipes():
                return False

        else:
            if not recipe.CookBook().update_recipes(recipes=args.update_recipes):
                return False

    # no recipe to install, exit
    if args.recipe is None:
        print('no recipe to build, exiting...')
        return True

    if args.uninstall:
        return uninstall_package(pkg=args.recipe,
                                 buildroot=buildroot,
                                 installdir=installdir,
                                 verbose=args.verbose)

    if args.clean:
        return clean(pkg=args.recipe,
                     buildroot=buildroot,
                     installdir=installdir,
                     verbose=args.verbose)

    # handle modes
    if args.mode is not None:
        EvalHandler.modes = set(args.mode)

    # default cmake args
    if args.cmake_args:
        cmake_tools.CmakeTools.set_default_args(['-D' + a for a in args.cmake_args])

    # print jobs
    print(f'building {args.recipe} with {args.jobs} parallel job{"s" if int(args.jobs) > 1 else ""}')

    if args.no_pwd:
        pwd = None
    elif args.debug_pwd:
        pwd = args.debug_pwd
    else:
        pwd = getpass.getpass()
        pprint('got password!')

    # perform required installation
    success = install_package(pkg=args.recipe,
                              srcroot=srcroot,
                              buildroot=buildroot,
                              installdir=installdir,
                              buildtype=args.default_build_type,
                              jobs=args.jobs,
                              reconfigure=args.force_reconfigure,
                              pwd=pwd
                              )

    return success


if __name__ == '__main__':
    main()