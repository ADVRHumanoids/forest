from tempfile import TemporaryDirectory
import os 

from forest.common import proc_utils

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

    return _call_cmake(['--build', self.builddir, '--target', target, '--', '-j', jobs])


def _call_cmake(args, cwd='.', print_on_error=True):

    args_str = list(map(str, args))
    return proc_utils.call_process(args=[cmake_command] + args_str, cwd=cwd, print_on_error=print_on_error)


def _find_package(pkg_name: str):
        
    with TemporaryDirectory(prefix="foresttmp-") as tmpdir:

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

