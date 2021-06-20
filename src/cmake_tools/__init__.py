
class CmakeTools:
    
    from ._impl import cmake_command

    def __init__(self, srcdir, builddir) -> None:
        from ._impl import _construct
        _construct(self, srcdir, builddir)

    def is_configured(self):
        from ._impl import _is_configured
        return _is_configured(self)

    def configure(self, args=list()):
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
