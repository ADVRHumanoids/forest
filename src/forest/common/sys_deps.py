"""
Utilities for installing system-level and pip dependencies declared in recipes
via ``system_depends`` and ``pip_depends`` fields.

Supported package managers (``--pkg-manager`` CLI flag):
  apt    – Debian/Ubuntu  (default on Linux if not overridden)
  dnf    – Fedora / RHEL
  brew   – macOS Homebrew
  conda  – Anaconda/Miniconda
  pacman – Arch Linux
"""

import shutil
import sys

from forest.common import proc_utils

# Global override set by main.py when --pkg-manager is passed
pkg_manager_override: str | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_pkg_manager() -> str:
    """Pick a sensible default based on what is available on PATH."""
    if pkg_manager_override is not None:
        return pkg_manager_override

    candidates = ['apt', 'dnf', 'pacman', 'brew', 'conda']
    for name in candidates:
        if shutil.which(name) is not None:
            return name

    return 'apt'  # last resort


def _system_install_cmd(manager: str, packages: list[str]) -> list[str]:
    """Return the command list to install *packages* with *manager*."""
    cmds = {
        'apt':    ['sudo', 'apt', 'install', '-y'] + packages,
        'dnf':    ['sudo', 'dnf', 'install', '-y'] + packages,
        'pacman': ['sudo', 'pacman', '-S', '--noconfirm'] + packages,
        'brew':   ['brew', 'install'] + packages,
        'conda':  ['conda', 'install', '-y'] + packages,
    }
    if manager not in cmds:
        raise ValueError(f"Unknown package manager '{manager}'. "
                         f"Supported: {', '.join(cmds)}")
    return cmds[manager]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def install_system_deps(packages: list[str], verbose: bool = False) -> bool:
    """Install *packages* using the system package manager."""
    if not packages:
        return True

    manager = _detect_pkg_manager()
    cmd = _system_install_cmd(manager, packages)

    print(f'[sys_deps] installing system packages via {manager}: {packages}')
    return proc_utils.call_process(args=cmd, verbose=verbose)


def install_pip_deps(packages: list[str], verbose: bool = False) -> bool:
    """Install *packages* via pip (uses the running interpreter)."""
    if not packages:
        return True

    cmd = ['python', '-m', 'pip', 'install'] + packages
    print(f'[sys_deps] installing pip packages: {packages}')
    return proc_utils.call_process(args=cmd, verbose=verbose)
