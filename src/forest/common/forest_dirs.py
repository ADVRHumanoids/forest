import os


def _find_ws_root(start: str) -> str:
    """Walk up from start directory until a .forest marker file is found."""
    current = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(current, '.forest')):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            # Reached filesystem root without finding a marker; fall back to cwd
            return os.getcwd()
        current = parent

rootdir = _find_ws_root(os.getcwd())
recipesdir = os.path.join(rootdir, 'recipes')
buildroot = os.path.join(rootdir, 'build')
installdir = os.path.join(rootdir, 'install')
srcroot = os.path.join(rootdir, 'src')

def update_dirs():
    global rootdir, recipesdir, buildroot, installdir, srcroot
    rootdir = _find_ws_root(os.getcwd())
    recipesdir = os.path.join(rootdir, 'recipes')
    buildroot = os.path.join(rootdir, 'build')
    installdir = os.path.join(rootdir, 'install')
    srcroot = os.path.join(rootdir, 'src')
