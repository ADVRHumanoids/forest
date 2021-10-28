from typing import List

class CmakeTools:
    
    from ._impl import cmake_command

    def __init__(self, srcdir, builddir) -> None:
        """
        Construct CmakeTools object for a package with given
        source directory and build directory

        Args:
            srcdir ([type]): [description]
            builddir ([type]): [description]
        """
        from ._impl import _construct
        _construct(self, srcdir, builddir)

    @staticmethod
    def set_default_args(args: List[str]):
        from ._impl import _set_default_args
        _set_default_args(args)

    def is_configured(self):
        """
        Check if this cmake project has been already configured, i.e.
        CMakeCache.txt exists.

        Returns:
            bool: True if already configured
        """
        from ._impl import _is_configured
        return _is_configured(self)

    def configure(self, args=None):
        """
        Configure the project by calling cmake with given arguments

        Args:
            args (list, optional): Arguments to be passed to cmake. Defaults to list().

        Returns:
            bool: True on success
        """
        from ._impl import _configure
        return _configure(self, args)

    def build(self, target='all', jobs=1):
        from ._impl import _build
        return _build(self, target, jobs)

    @staticmethod
    def find_package(pkg_name: str) -> bool:
        from ._impl import _find_package
        return _find_package(pkg_name=pkg_name)

    @staticmethod
    def call_cmake(args, cwd='.'):
        from ._impl import _call_cmake
        return _call_cmake(args, cwd)
