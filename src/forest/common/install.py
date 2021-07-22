from genericpath import exists
import os

from forest.cmake_tools import CmakeTools
from forest.git_tools import GitTools
from . import package

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
def install_package(pkg: str,
                    srcroot: str,
                    buildroot: str,
                    installdir: str,
                    buildtype: str,
                    jobs: int,
                    reconfigure=False):
    
    """
    Fetch a recipe file from the default path using the given package name, 
    and perform the required cloning and building steps of the package and 
    its dependencies

    Returns:
        bool: success flag
    """

    # retrieve package info from recipe
    try:
        pkg = package.Package.from_name(name=pkg)
    except FileNotFoundError:
        print(f'[{pkg}] recipe file not found (searched in {package.Package.get_recipe_path()})')
        return False

    # install dependencies if not found
    for dep in pkg.depends:

        dep_found = CmakeTools.find_package(dep)
        dep_builddir = os.path.join(buildroot, dep)

        if not dep_found:
            # dependency not found -> install it
            print(f'[{pkg.name}] depends on {dep} -> not found, installing..')
            ok = install_package(dep, srcroot, buildroot, installdir, buildtype, jobs, reconfigure)   # reconfigure needed if there's build but not install
            if not ok:
                print(f'[{pkg.name}] failed to install dependency {dep}')
                return False
        elif os.path.exists(dep_builddir):
            # dependency found and built by forest -> trigger build
            print(f'[{pkg.name}] depends on {dep} -> build found, building..')   

            # retrieve package info from recipe
            try:
                debpkg = package.Package.from_name(name=dep)
            except FileNotFoundError:
                print(f'[{pkg}] recipe file not found (searched in {package.Package.get_recipe_path()})')
                return False
            
            # build
            ok = build_package(pkg=debpkg, 
                               srcroot=srcroot, 
                               buildroot=buildroot, 
                               installdir=installdir, 
                               buildtype=buildtype, 
                               jobs=jobs,
                               reconfigure=reconfigure)
            if not ok:
                print(f'[{pkg.name}] failed to build dependency {dep}')
                return False 
        else:
            # dependency found and not built by forest -> nothing to do
            print(f'[{pkg.name}] depends on {dep} -> found')
    
    # use the fetcher!
    srcdir = os.path.join(srcroot, pkg.name)
    if not pkg.fetcher.fetch(srcdir):
        print(f'[{pkg.name}] failed to fetch package')
        return False 
    
    # configure and build
    ok = build_package(pkg=pkg, 
                       srcroot=srcroot, 
                       buildroot=buildroot, 
                       installdir=installdir, 
                       buildtype=buildtype, 
                       jobs=jobs, 
                       reconfigure=reconfigure)

    if ok:
        print(f'[{pkg.name}] ok')

    return ok


def write_setup_file(installdir):
    
    """
    Write a setup file to the given installdir directory.
    """

    this_dir = os.path.dirname(os.path.abspath(__file__))
    setup_template = os.path.join(this_dir, 'setup.bash')
    with open(setup_template, 'r') as f:
        content = f.read()
        content = content.replace('£PREFIX£', os.path.realpath(installdir))
    
    setup_file = os.path.join(installdir, 'setup.bash')
    if not os.path.exists(setup_file):
        with open(setup_file, 'w') as f:
            f.write(content)


def check_ws_file(rootdir):
    
    """
    Write a hidden file to mark the forest root directory
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

