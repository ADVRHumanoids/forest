import os

from forest.cmake_tools import CmakeTools
from . import package
from .print_utils import ProgressReporter
from .forest_dirs import *
from forest.common import proc_utils
from forest.common.recipe import Cookbook

_build_cache = dict()

def build_package(pkg: package.Package, 
                  srcroot: str, 
                  buildroot: str, 
                  installdir: str,
                  buildtype: str,
                  jobs: int,
                  reconfigure=False):

    # source dir and build dir
    srcdir = os.path.join(srcroot, pkg.name)
    builddir = os.path.join(buildroot, pkg.name)

    # doit!
    return pkg.builder.build(srcdir=srcdir, builddir=builddir, installdir=installdir,
                      buildtype=buildtype, jobs=jobs, reconfigure=reconfigure)



# function to install one package with dependencies
@ProgressReporter.count_calls
def install_package(pkg: str,
                    srcroot: str,
                    buildroot: str,
                    installdir: str,
                    buildtype: str,
                    jobs: int,
                    reconfigure=False, 
                    no_deps=False,
                    src_only=False):
    
    """
    Fetch a recipe file from the default path using the given package name, 
    and perform the required cloning and building steps of the package and 
    its dependencies

    Returns:
        bool: success flag
    """

    # custom print
    pprint = ProgressReporter.get_print_fn(pkg)

    # retrieve package info from recipe
    try:
        pkg = package.Package.from_name(name=pkg)
    except FileNotFoundError:
        pprint(f'recipe file not found (searched in {Cookbook.get_recipe_path()})')
        return False

    # install dependencies if not found
    for dep in pkg.depends:
        
        # if no-deps mode, skip dependency installation
        if no_deps:
            pprint(f'skipping dependency {dep}')
            continue

        # this dependency build directory name (if exists)
        dep_builddir = os.path.join(buildroot, dep)

        # if dependency is built by this ws, trigger build
        if os.path.exists(dep_builddir):
            
            # dependency found and built by forest -> trigger build
            pprint(f'depends on {dep} -> build found, building..')   

            ok = install_package(dep, srcroot, buildroot, installdir, 
                    buildtype, jobs, reconfigure, no_deps=no_deps, src_only=src_only)   

            if not ok:
                pprint(f'failed to build dependency {dep}')
                return False 

            # go to next dependency
            continue

        # try to find-package this dependency
        dep_found = CmakeTools.find_package(dep)

        if not dep_found:
            # dependency not found -> install it
            pprint(f'depends on {dep} -> not found, installing..')
            
            # note: reconfigure needed if there's build but not install
            ok = install_package(dep, srcroot, buildroot, installdir, 
                    buildtype, jobs, reconfigure, no_deps=no_deps, src_only=src_only)

            if not ok:
                pprint(f'failed to install dependency {dep}')
                return False

        else:
            # dependency found and not built by forest -> nothing to do
            pprint(f'depends on {dep} -> found')
    
    srcdir = os.path.join(srcroot, pkg.name)
    if not pkg.fetcher.fetch(srcdir):
        pprint('failed to fetch package')
        return False 
    
    # configure and build
    if src_only:
        pprint('src_only mode: will not build')
        ok = True
    else:
        ok = build_package(pkg=pkg, 
                        srcroot=srcroot, 
                        buildroot=buildroot, 
                        installdir=installdir, 
                        buildtype=buildtype, 
                        jobs=jobs, 
                        reconfigure=reconfigure)

    if ok:
        pprint('ok')

    return ok


def uninstall_package(pkg: str,
                      buildroot: str,
                      installdir: str,
                      verbose: bool):

    # custom print
    pprint = ProgressReporter.get_print_fn(pkg)

    try:
        pkg = package.Package.from_name(name=pkg)
    except FileNotFoundError:
        pprint(f'recipe file not found (searched in {Cookbook.get_recipe_basedir()})')
        return False

    install_cache_fname = os.path.join(installdir, ".install_cache", pkg.name)
    if not os.path.isfile(install_cache_fname):
        pprint(f"missing information: {install_cache_fname}\nare you sure the recipe '{pkg.name}' is installed?")
        return False

    error = False
    with open(install_cache_fname, 'r') as install_cache:
        for file in install_cache.readlines():
            fname = str(file).rstrip()
            if not _remove_fname(pkg.name, fname, installdir, verbose):
                error = True

    if not error:
        cmd = ['rm', install_cache_fname]
        ok = proc_utils.call_process(args=cmd, print_on_error=verbose)
        
        pprint('uninstalled successfully')
        return True

    return False


def _remove_fname(pkg: str, fname: str, installdir:str, verbose: bool):

    # custom print
    pprint = ProgressReporter.get_print_fn(pkg)

    if fname == installdir:
        return True

    if not os.path.islink(fname) and not os.path.exists(fname):
        if verbose:
            pprint(f'removing:  {fname} --> no such file or directory')
        fname = os.path.split(fname)[0]
        return _remove_fname(pkg, fname, installdir, verbose)

    elif not os.path.isdir(fname) or len(os.listdir(fname)) == 0:
        if verbose:
            pprint(f'removing:  {fname}', end="")
        cmd = ['rm', '-r', fname]
        ok = proc_utils.call_process(args=cmd, print_on_error=verbose)
        if ok:
            if verbose:
                print(' --> done')
            fname = os.path.split(fname)[0]
            return _remove_fname(pkg, fname, installdir, verbose)

        else:
            if verbose:
                print(' --> error removing file or directory')
            return False

    return True


def clean(pkg: str, buildroot: str,  installdir: str, verbose: bool):
    pprint = ProgressReporter.get_print_fn(pkg)      
    return _remove_buildir(pkg, verbose)


def _remove_buildir(pkg, verbose):
    builddir = os.path.join(buildroot, pkg)
    pprint = ProgressReporter.get_print_fn(pkg)
    pprint(f'removing build directory: {builddir}')
    cmd = ['rm', '-r', builddir]
    ok = proc_utils.call_process(args=cmd, print_on_error=verbose)
    if ok:
        pprint('build directory removed successfully')

    return ok


def write_setup_file():
    
    """
    Write a setup file to the root directory.
    """

    # compute relative site-package path 
    # without using distutils, which is deprecated
    import sys 
    import sysconfig
    import site
    platlib_path = sysconfig.get_path(name='platlib')    
    platlib_relpath = os.path.relpath(path=site.USER_SITE, start=site.USER_BASE)

    # replace placeholders
    this_dir = os.path.dirname(os.path.abspath(__file__))
    setup_template = os.path.join(this_dir, 'setup.bash')
    with open(setup_template, 'r') as f:
        content = f.read()
        content = content.replace('£PREFIX£', os.path.realpath(installdir))
        content = content.replace('£SRCDIR£', os.path.realpath(srcroot))
        content = content.replace('£ROOTDIR£', os.path.realpath(rootdir))
        content = content.replace('£REL_SITE_PKG_PATH£', platlib_relpath)
    
    setup_file = os.path.join(installdir, '..', 'setup.bash')
    if not os.path.exists(setup_file):
        with open(setup_file, 'w') as f:
            f.write(content)


def check_ws_file(rootdir):
    
    """
    Check forest marker file exists
    """

    ws_file = os.path.join(rootdir, '.forest')

    return os.path.exists(ws_file)


def write_ws_file(rootdir):
    
    """
    Write a hidden file to mark the forest root directory
    """
    
    ws_file = os.path.join(rootdir, '.forest')

    if check_ws_file(rootdir=rootdir):
        print('workspace already initialized')
        return False

    with open(ws_file, 'w') as f:
        f.write('# forest marker file \n')
        return True

def create_ws_venv(rootdir):
    
    venv_name = os.path.basename(rootdir)
    
    if venv_name[-3:] == '_ws':
        venv_name = venv_name[:-3] + '_venv'
    else:
        venv_name = venv_name + '_venv'
    
    if os.path.exists(f'{rootdir}/{venv_name}'):
        return True
    
    print(f'creating virtual environment "{venv_name}"')

    ok = proc_utils.call_process(f'/usr/bin/env python3 -m venv --system-site-packages {rootdir}/{venv_name}'.split())
    
    if not ok:
        print('creating virtual environment failed')
        return False 
    
    os.symlink(f'{venv_name}', f'venv')