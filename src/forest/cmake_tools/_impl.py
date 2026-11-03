from tempfile import TemporaryDirectory
import os 
from functools import partial

from forest.common import proc_utils
from forest.common.parser import make_regrex_pattern


cmake_command = 'cmake'
default_args = list()

def _construct(self, srcdir, builddir):
    self.srcdir = srcdir
    self.builddir = builddir

def _is_configured(self):

    return os.path.exists(os.path.join(self.builddir, 'Makefile'))

def _set_default_args(args):
    global default_args
    default_args = args

def _configure(self, args):

    if args is None:
        args = list()

    return _call_cmake([self.srcdir] + args + default_args, cwd=self.builddir)
    

def _build(self, target, jobs):

    return _call_cmake(['--build', self.builddir, '--target', target, '--', '-j', jobs], print_progress=True)


def _call_cmake(args, cwd='.', print_on_error=True, print_progress=False):

    args_str = list(map(str, args))
    update_regrex_pattern = make_regrex_pattern if print_progress else None
    return proc_utils.call_process(args=[cmake_command] + args_str,
                                   cwd=cwd, 
                                   print_on_error=print_on_error,
                                   update_regrex_pattern=update_regrex_pattern)


def _find_package(pkg_name: str, version=None, exact=False, prefix_path=None):
    from forest.common.dependency import Dependency
    dep = Dependency(pkg_name, version, exact)
        
    with TemporaryDirectory(prefix="foresttmp-") as tmpdir:

        # dir of current file
        cmake_tools_dir = os.path.dirname(os.path.abspath(__file__))
        
        # open template
        with open(os.path.join(cmake_tools_dir, 'template', 'find_package.txt'), 'r') as f:
            find_package_tpl = f.read()
        
        # configure template
        srcdir = find_package_tpl.replace('£PKG_NAME', dep.name)
        srcdir = srcdir.replace('£VERSION_ARGS',
                                '' if dep.version is None else
                                dep.version + (' EXACT' if dep.exact else ''))

        # write it to tmp dir
        cmakelists_path = os.path.join(tmpdir, 'CMakeLists.txt')
        with open(cmakelists_path, 'w') as f:
            f.write(srcdir)
        
        args = ['.']
        if prefix_path is not None:
            args.append('-DCMAKE_PREFIX_PATH=' + os.path.abspath(prefix_path))
        return _call_cmake(args + default_args, cwd=tmpdir, print_on_error=False)

