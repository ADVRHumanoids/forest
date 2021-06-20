import argparse
import os
from typing import List

from cmake_tools import CmakeTools
from git_tools import GitTools
from common import package

parser = argparse.ArgumentParser(description='forest automatizes cloning and building of software packages')
parser.add_argument('recipe', help='name of recipe with fetch and build information')
parser.add_argument('--verbose', '-v', required=False, action='store_true', help='print additional information')
args = parser.parse_args()


def install_package(pkg : str):

    # retrieve package info from recipe
    pkg = package.Package.from_name(name=pkg)

    # install dependencies if not found
    for dep in pkg.depends:
        dep_found = CmakeTools.find_package(dep)
        if not dep_found:
            print(f'[{pkg.name}] depends on {dep} which was not found, installing..')
            install_package(pkg=dep)
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
        print(f'[{pkg.name}] unable to clone source code, skipping..')
        return False

    elif not git.checkout(tag=pkg.git_tag):
        print(f'[{pkg.name}] unable to checkout tag {pkg.git_tag}, skipping..')
        
    # create cmake tools
    cmakelists = os.path.join(srcdir, pkg.cmakelists)
    builddir = os.path.join(buildroot, pkg.name)
    if not os.path.exists(builddir):
        os.mkdir(builddir)
    cmake = CmakeTools(srcdir=cmakelists, builddir=builddir)

    # set install prefix and build type (only on first configuration)
    cmake_args = list(pkg.cmake_args)
    if not cmake.is_configured():
        cmake_args.append(f'-DCMAKE_INSTALL_PREFIX={installdir}')
        cmake_args.append(f'-DCMAKE_BUILD_TYPE={buildtype}')

    # configure
    print(f'[{pkg.name}] running cmake...')
    if not cmake.configure(args=cmake_args):
        print(f'[{pkg.name}] configuring failed')
        return False

    # build
    print(f'[{pkg.name}] building...')
    if not cmake.build(target=pkg.target, jobs=8):
        print(f'[{pkg.name}] build failed')
        return False 

    print(f'[{pkg.name}] ok')
    return True
    

rootdir = os.getcwd()
buildroot = os.path.join(rootdir, 'build')
installdir = os.path.join(rootdir, 'install')
srcroot = os.path.join(rootdir, 'src')
buildtype = 'Release'

for dir in (buildroot, installdir, srcroot):
    if not os.path.exists(dir):
        os.mkdir(dir)

success = install_package(args.recipe)

exit(0 if success else 1)