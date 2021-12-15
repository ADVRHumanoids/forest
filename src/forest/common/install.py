import os

from forest.cmake_tools import CmakeTools
from . import package
from .print_utils import ProgressReporter
from forest.common import proc_utils

_build_cache = dict()

def build_package(pkg: package.Package, 
                  srcroot: str, 
                  buildroot: str, 
                  installdir: str,
                  buildtype: str,
                  jobs: int,
                  reconfigure=False,
                  pwd=None):

    # source dir and build dir
    srcdir = os.path.join(srcroot, pkg.name)
    builddir = os.path.join(buildroot, pkg.name)

    # doit!
    return pkg.builder.build(srcdir=srcdir, builddir=builddir, installdir=installdir,
                      buildtype=buildtype, jobs=jobs, reconfigure=reconfigure, pwd=pwd)



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
                    pwd=None):
    
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
        pprint(f'recipe file not found (searched in {package.Package.get_recipe_path()})')
        return False

    # install dependencies if not found
    for dep in pkg.depends:

        # if no-deps mode, skip the loop!
        if no_deps:
            pprint('skipping dependencies')
            break
        
        # try to find-package this dependency
        dep_found = CmakeTools.find_package(dep)

        # this dependency build directory name (if exists)
        dep_builddir = os.path.join(buildroot, dep)

        if not dep_found:
            # dependency not found -> install it
            pprint(f'depends on {dep} -> not found, installing..')
            
            # note: reconfigure needed if there's build but not install
            ok = install_package(dep, srcroot, buildroot, installdir, 
                    buildtype, jobs, reconfigure, pwd=pwd)

            if not ok:
                pprint(f'failed to install dependency {dep}')
                return False

        elif os.path.exists(dep_builddir):
            # dependency found and built by forest -> trigger build
            pprint(f'depends on {dep} -> build found, building..')   

            ok = install_package(dep, srcroot, buildroot, installdir, 
                    buildtype, jobs, reconfigure, no_deps=True, pwd=pwd)   

            if not ok:
                pprint(f'failed to build dependency {dep}')
                return False 
        else:
            # dependency found and not built by forest -> nothing to do
            pprint(f'depends on {dep} -> found')
    
    srcdir = os.path.join(srcroot, pkg.name)
    if not pkg.fetcher.fetch(srcdir, pwd=pwd):
        pprint('failed to fetch package')
        return False 
    
    # configure and build
    ok = build_package(pkg=pkg, 
                       srcroot=srcroot, 
                       buildroot=buildroot, 
                       installdir=installdir, 
                       buildtype=buildtype, 
                       jobs=jobs, 
                       reconfigure=reconfigure,
                       pwd=pwd)

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
        pprint(f'recipe file not found (searched in {package.Package.get_recipe_path()})')
        return False

    builddir = os.path.join(buildroot, pkg.name)
    manifest_fname = os.path.join(builddir, 'install_manifest.txt')
    if not os.path.isfile(manifest_fname):
        pprint(f'missing install_manifest.txt: {manifest_fname}')
        return False

    error = False
    with open(manifest_fname, 'r') as manifest:
        for file in manifest.readlines():
            fname = str(file).rstrip()
            if not _remove_fname(pkg.name, fname, installdir, verbose):
                error = True

    if not error:
        pprint('uninstalled successfully')
        return True

    pprint('errors occurred during uninstallation')
    return False


def _remove_fname(pkg: str, fname: str, installdir:str, verbose: bool):

    # custom print
    pprint = ProgressReporter.get_print_fn(pkg)

    if fname == installdir:
        return True

    pprint(f'removing:  {fname}', end="")
    cmd = ['rm', '-r', fname]
    ok = proc_utils.call_process(args=cmd, print_on_error=verbose)
    if ok:
        print(' --> done')
        dirname = os.path.split(fname)[0]
        if len(os.listdir(dirname)) == 0:
            return _remove_fname(pkg, dirname, installdir, verbose)

        return True

    else:
        print(' --> error')
        return False




def write_setup_file(srcdir, installdir):
    
    """
    Write a setup file to the root directory.
    """

    this_dir = os.path.dirname(os.path.abspath(__file__))
    setup_template = os.path.join(this_dir, 'setup.bash')
    with open(setup_template, 'r') as f:
        content = f.read()
        content = content.replace('£PREFIX£', os.path.realpath(installdir))
        content = content.replace('£SRCDIR£', os.path.realpath(srcdir))
    
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

