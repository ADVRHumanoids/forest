from tempfile import TemporaryDirectory
import os 
import sys
import subprocess

from common import proc_utils

cmake_command = 'cmake'

def _construct(self, srcdir, builddir):
    self.srcdir = srcdir
    self.builddir = builddir

def _is_configured(self):

    return os.path.exists(os.path.join(self.builddir, 'CMakeCache.txt'))

def _configure(self, args):

    return _call_cmake([self.srcdir, '-B', self.builddir] + args)
    

def _build(self, target, jobs):

    return _call_cmake(['--build', self.builddir, '--target', target, '-j', jobs])


def _call_cmake(args, cwd='.', print_on_error=True):

    args_str = list(map(str, args))
    return proc_utils.call_process(args=[cmake_command] + args_str, cwd=cwd, print_on_error=print_on_error)


def _find_package(pkg_name: str):
        
    with TemporaryDirectory(prefix="tmake-") as tmpdir:

        # dir of current file
        cmake_tools_dir = os.path.dirname(os.path.abspath(__file__))
        
        # open template
        with open(os.path.join(cmake_tools_dir, 'template', 'find_package.txt'), 'r') as f:
            find_package_tpl = f.read()
        
        # configure template
        srcdir = find_package_tpl.replace('£PKG_NAME', pkg_name)

        # write it to tmp dir
        cmakelists_path = os.path.join(tmpdir, 'CMakeLists.txt')
        with open(cmakelists_path, 'w') as f:
            f.write(srcdir)
        
        return _call_cmake('.', cwd=tmpdir, print_on_error=False)

