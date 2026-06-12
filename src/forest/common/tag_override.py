import json
from pathlib import Path


TAG_OVERRIDE_FILE_SUFFIXES = ('.lock', '.yaml', '.yml', '.json')


def _validate_tag_overrides(overrides, parser, source):
    if overrides is None:
        return {}

    if not isinstance(overrides, dict):
        parser.error(f'--tag-override {source} must contain a mapping of package names to tags')

    ret = {}
    for pkgname, tag in overrides.items():
        pkgname = str(pkgname)
        if not pkgname:
            parser.error(f'--tag-override {source} contains an empty package name')
        if tag is None or str(tag) == '':
            parser.error(f'--tag-override {source} contains an empty tag for package {pkgname}')
        ret[pkgname] = str(tag)

    return ret


def _load_tag_override_file(filename, parser):
    suffix = Path(filename).suffix.lower()

    try:
        with open(filename, 'r') as f:
            if suffix == '.json':
                overrides = json.load(f)
            else:
                import yaml
                overrides = yaml.safe_load(f)
    except OSError as e:
        parser.error(f'could not read --tag-override file {filename}: {e}')
    except json.JSONDecodeError as e:
        parser.error(f'could not parse --tag-override JSON file {filename}: {e}')
    except Exception as e:
        if e.__class__.__module__.startswith('yaml'):
            parser.error(f'could not parse --tag-override YAML file {filename}: {e}')
        raise

    return _validate_tag_overrides(overrides, parser, filename)


def _parse_inline_tag_overrides(entries, parser):
    overrides = {}

    for entry in entries:
        if ':=' not in entry:
            parser.error('--tag-override with multiple values requires pkg:=tag entries')

        pkgname, tag = entry.split(':=', 1)
        if not pkgname:
            parser.error(f'--tag-override entry {entry} has an empty package name')
        if not tag:
            parser.error(f'--tag-override entry {entry} has an empty tag')
        if pkgname in overrides:
            parser.error(f'--tag-override contains duplicate entry for package {pkgname}')

        overrides[pkgname] = tag

    return overrides


def parse_tag_overrides(tag_override, recipes, parser):
    if len(tag_override) == 1:
        tag_or_file = tag_override[0]
        if tag_or_file.lower().endswith(TAG_OVERRIDE_FILE_SUFFIXES):
            return _load_tag_override_file(tag_or_file, parser)

        if len(recipes) != 1:
            parser.error('--tag-override TAG can only be used when growing exactly one recipe')
        if tag_or_file == '':
            parser.error('--tag-override TAG cannot be empty')

        return {recipes[0]: tag_or_file}

    return _parse_inline_tag_overrides(tag_override, parser)
