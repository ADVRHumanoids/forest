"""Recipe dependencies and their optional CMake version requirements."""

import re


class Dependency:
    def __init__(self, name, version=None, exact=False):
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.+\-]*', name):
            raise ValueError('dependency name must be a nonempty package name')
        if version is not None and (
                not isinstance(version, str) or
                not re.fullmatch(r'[0-9]+(?:\.[0-9]+){0,3}', version)):
            raise ValueError('dependency version must be a quoted numeric version (e.g. "2.6.1")')
        if not isinstance(exact, bool):
            raise ValueError('dependency exact must be a boolean')
        if exact and version is None:
            raise ValueError('dependency exact requires a version')
        self.name = name
        self.version = version
        self.exact = exact

    @classmethod
    def from_yaml(cls, value):
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(value)
        if not isinstance(value, dict) or 'name' not in value:
            raise ValueError('dependency must be a name or a mapping with name, version, and optional exact')
        unknown = set(value) - {'name', 'version', 'exact'}
        if unknown:
            raise ValueError('unknown dependency fields: ' + ', '.join(map(str, unknown)))
        return cls(**value)

    def __str__(self):
        if self.version is None:
            return self.name
        return '{} {}{}'.format(self.name, self.version, ' EXACT' if self.exact else '')
