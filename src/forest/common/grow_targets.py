from pathlib import Path


def get_current_src_package(cwd, srcroot):
    cwd = Path(cwd).resolve()
    srcroot = Path(srcroot).resolve()

    try:
        relative_path = cwd.relative_to(srcroot)
    except ValueError:
        return None

    if not relative_path.parts:
        return None

    return relative_path.parts[0]


def is_workspace_root(cwd, rootdir):
    return Path(cwd).resolve() == Path(rootdir).resolve()


def get_workspace_src_recipes(srcroot, available_recipes, blacklist=None):
    srcroot = Path(srcroot)
    available_recipes = set(available_recipes)
    blacklist = set(blacklist or [])

    recipes = []
    warnings = []

    if not srcroot.exists():
        return recipes, warnings

    for path in sorted(srcroot.iterdir(), key=lambda p: p.name):
        if not path.is_dir():
            continue

        pkgname = path.name
        if pkgname in blacklist:
            continue

        if pkgname not in available_recipes:
            warnings.append(f'[forest] warning: package {pkgname} has no available recipe, skipping')
            continue

        recipes.append(pkgname)

    return recipes, warnings
