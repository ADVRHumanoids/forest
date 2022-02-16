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
    recipe.Cookbook.basedir = recipesdir

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
    parser.add_argument('--list', '-l', required=False, action='store_true', help='list available recipes')
    parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print additional information')
    parser.add_argument('--log-file', default=dfl_log_file, help='log file for non-verbose mode')

    subparsers = parser.add_subparsers(dest='command')

    grow_cmd = 'grow'
    grow_parser = subparsers.add_parser(grow_cmd, help='add recipes from git remote')
    grow_parser.add_argument('recipe', nargs='?', choices=available_recipes, help='name of recipe with fetch and build information')
    grow_parser.add_argument('--jobs', '-j', default=1, help='parallel jobs for building')
    grow_parser.add_argument('--mode', '-m', nargs='+', required=False, help='specify modes that are used to set conditional compilation flags (e.g., cmake args)')
    grow_parser.add_argument('--config', '-c', nargs='+', required=False, help='specify configuration variables that can be used inside recipes')
    grow_parser.add_argument('--default-build-type', '-t', default=buildtypes[1], choices=buildtypes, help='build type for cmake, it is overridden by recipe')
    grow_parser.add_argument('--force-reconfigure', required=False, action='store_true', help='force calling cmake before building with args from the recipe')
    grow_parser.add_argument('--list-eval-locals', required=False, action='store_true', help='print available attributes when using conditional build args')
    grow_parser.add_argument('--clone-protocol', required=False, choices=cloneprotos, help='override clone protocol')
    grow_parser.add_argument('--cmake-args', nargs='+', required=False, help='specify additional cmake args to be appended to each recipe (leading -D must be omitted)')
    grow_parser.add_argument('--no-deps', '-n', required=False, action='store_true', help='skip dependency fetch and build step')
    command_group = grow_parser.add_mutually_exclusive_group()
    command_group.add_argument('--no-pwd', required=False, action='store_true', help='do not prompt for password at the beginning')
    command_group.add_argument('--debug-pwd', default=None, help='')
    grow_parser.add_argument('--uninstall', required=False, action='store_true', help='uninstall recipe')
    grow_parser.add_argument('--clean', required=False, action='store_true', help='uninstall recipe and remove build')

    recipes_cmd = 'add-recipes'
    recipes_parser = subparsers.add_parser(recipes_cmd, help='add recipes from git remote')
    recipes_parser.add_argument('url', help='url of the remote (e.g. git@github.com:<username>/<reponame>.git)')
    recipes_parser.add_argument('--tag', '-t', required=False, default='master')
    recipes_parser.add_argument('--subdir-path', '-s', required=False, default='recipes', help='relative path to the folder in which recipes are contained')
    recipes_parser.add_argument('--recipes', '-r', required=False, nargs='+', help='specify which recipes to add, otherwise all recipes in subdir-path are added')
    recipes_parser.add_argument('--allow_overwrite', '-o', required=False, action='store_true', help='allow overwritng local recipes with new ones')

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # initialize workspace
    if args.init:
        # create marker file
        write_ws_file(rootdir=rootdir)  # note: error on failure?

    # check ws
    if not check_ws_file(rootdir=rootdir):
        print(f'current directory {rootdir} is not a forest workspace.. \
    have you called forest --init ?', file=sys.stderr)
        return False

    # create directories
    for dir in (buildroot, installdir, srcroot, recipesdir):
        if not os.path.exists(dir):
            os.mkdir(dir)

    # create setup.bash if does not exist
    write_setup_file(srcdir=srcroot, installdir=installdir)

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
    if args.command == grow_cmd and args.config:
        from forest.common import config_handler
        ch = config_handler.ConfigHandler.instance()
        ch.set_config_variables(args.config)

    # print available local attributes for conditional args
    if args.command == grow_cmd and args.list_eval_locals:
        from forest.common import eval_handler
        eval_handler.EvalHandler.print_available_locals()
        return True

    # clone proto
    if args.command == grow_cmd and args.clone_protocol is not None:
        from forest.common.fetch_handler import GitFetcher
        GitFetcher.proto_override = args.clone_protocol

    if args.command == recipes_cmd:
        print('adding recipes...')
        recipe_source = recipe.RecipeSource.FromUrl(args.url, args.tag)
        recipe.Cookbook.add_recipes(recipe_source, args.recipes, args.subdir_path, args.allow_overwrite)
        return True

    # no recipe to install, exit
    if args.command == grow_cmd and args.recipe is None:
        print('no recipe to build, exiting...')
        return True

    if args.command == grow_cmd and args.uninstall:
        return uninstall_package(pkg=args.recipe,
                                 buildroot=buildroot,
                                 installdir=installdir,
                                 verbose=args.verbose)

    if args.command == grow_cmd and args.clean:
        return clean(pkg=args.recipe,
                     buildroot=buildroot,
                     installdir=installdir,
                     verbose=args.verbose)

    # handle modes
    if args.command == grow_cmd and args.mode is not None:
        EvalHandler.modes = set(args.mode)

    # default cmake args
    if args.command == grow_cmd and args.cmake_args:
        cmake_tools.CmakeTools.set_default_args(['-D' + a for a in args.cmake_args])

    # print jobs
    if args.command == grow_cmd:
        print(f'building {args.recipe} with {args.jobs} parallel job{"s" if int(args.jobs) > 1 else ""}')

        if args.command == grow_cmd and args.no_pwd:
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