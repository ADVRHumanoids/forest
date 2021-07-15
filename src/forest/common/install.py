from genericpath import exists
import os

from forest.cmake_tools import CmakeTools
from forest.git_tools import GitTools
from . import package

_build_cache = dict()

def build_package(pkgname: str, 
                  srcroot: str, 
                  buildroot: str, 
                  installdir: str,
                  buildtype: str,
                  jobs: int,
                  reconfigure=False):

    if pkgname in _build_cache.keys():
        print(f'[{pkgname}] already built, skipping')
        return True

    # retrieve package info from recipe
    try:
        pkg = package.Package.from_name(name=pkgname)
    except FileNotFoundError:
        print(f'[{pkgname}] recipe file not found (searched in {package.Package.get_recipe_path()})')
        return False

    # source dir
    srcdir = os.path.join(srcroot, pkg.name)

    # create cmake tools
    cmakelists = os.path.join(srcdir, pkg.cmakelists)
    builddir = os.path.join(buildroot, pkg.name)
    if not os.path.exists(builddir):
        os.mkdir(builddir)
    cmake = CmakeTools(srcdir=cmakelists, builddir=builddir)

    cmake_args = list()
    # configure
    if not cmake.is_configured() or reconfigure:
        # set install prefix and build type (only on first or forced configuration)
        cmake_args.append(f'-DCMAKE_INSTALL_PREFIX={installdir}')
        cmake_args.append(f'-DCMAKE_BUILD_TYPE={buildtype}')
        cmake_args += pkg.cmake_args  # note: flags from recipes as last entries to allow override

        print(f'[{pkg.name}] running cmake...')
        if not cmake.configure(args=cmake_args):
            print(f'[{pkg.name}] configuring failed')
            return False

    # build
    print(f'[{pkg.name}] building...')
    if not cmake.build(target=pkg.target, jobs=jobs):
        print(f'[{pkg.name}] build failed')
        return False 
    
    # save to cache and exit
    _build_cache[pkgname] = True
    return True


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
            print(f'[{pkg.name}] depends on {dep} -> not found, installing..')
            ok = install_package(dep, srcroot, buildroot, installdir, buildtype, jobs)
            if not ok:
                print(f'[{pkg.name}] failed to install dependency {dep}')
                return False
        elif os.path.exists(dep_builddir):
            print(f'[{pkg.name}] depends on {dep} -> build found, building..')   
            ok = build_package(pkgname=dep, 
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
            print(f'[{pkg.name}] depends on {dep} -> found')
    
    # if basic package, stop here
    if not isinstance(pkg, package.Package):
        return True

    # pkg is a full Package type
    pkg : package.Package = pkg

    # create git tools
    srcdir = os.path.join(srcroot, pkg.name)
    git = GitTools(srcdir=srcdir)

    # clone & checkout tag
    print(f'[{pkg.name}] cloning source code ...')
    if os.path.exists(srcdir):
        print(f'[{pkg.name}] source code  already exists, skipping clone')

    elif not git.clone(server=pkg.git_server, repository=pkg.git_repo, proto='ssh'):
        print(f'[{pkg.name}] unable to clone source code')
        return False

    elif not git.checkout(tag=pkg.git_tag):
        print(f'[{pkg.name}] unable to checkout tag {pkg.git_tag}')
        return False
    
    # configure and build
    ok = build_package(pkgname=pkg.name, 
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

