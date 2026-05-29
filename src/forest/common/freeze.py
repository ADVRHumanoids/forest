import os
import subprocess
import sys

import yaml

import forest.common.forest_dirs as _forest_dirs


def freeze(append: bool = False, ignore_errors: bool = False) -> bool:
    srcroot = _forest_dirs.srcroot
    rootdir = _forest_dirs.rootdir
    lock_file = os.path.join(rootdir, 'forest.lock')

    if not os.path.isdir(srcroot):
        print(f'src directory not found: {srcroot}', file=sys.stderr)
        return False

    pkgs = sorted([
        d for d in os.listdir(srcroot)
        if os.path.isdir(os.path.join(srcroot, d))
    ])

    entries = {}
    errors = []

    for pkg in pkgs:
        pkgdir = os.path.join(srcroot, pkg)

        # check it is a git repo
        is_git = subprocess.run(
            ['git', 'rev-parse', '--git-dir'],
            cwd=pkgdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        ).returncode == 0
        if not is_git:
            errors.append(f'{pkg}: not a git repository')
            continue

        # check for local changes
        status = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=pkgdir, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
        if status.stdout.strip():
            errors.append(f'{pkg}: has uncommitted local changes')
            continue

        # get HEAD sha1
        sha1 = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=pkgdir, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        ).stdout.strip()
        entries[pkg] = sha1

    if errors:
        for e in errors:
            print(f'error: {e}', file=sys.stderr)
        if not ignore_errors:
            return False

    if append and os.path.isfile(lock_file):
        with open(lock_file, 'r') as f:
            existing = yaml.safe_load(f) or {}
        existing.update(entries)
        entries = existing

    with open(lock_file, 'w') as f:
        yaml.dump(entries, f, default_flow_style=False)

    print(f'wrote {lock_file} ({len(entries)} package{"s" if len(entries) != 1 else ""})')
    return True
