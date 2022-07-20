
import os
import re

from forest.git_tools import *
from parse import parse
# - clone repository (with given branch) into recipes/src
# - symlink all .yaml files from recipes/src/repo/tag/subdir to recipes
# - handle conflicts, as follows
#   * in default mode, choose which source to keep
#   * with --allow-recipe-overwrite, last file is used and an informative message is printed

__all__ = ['RecipeSource', 'Cookbook']


class DuplicateRecipes(Exception):
    pass


class UserInterrupt(Exception):
    pass


class RecipeSource:
    def __init__(self, server: str, username: str, repository: str, tag: str, protocol: str):
        self.server = server
        self.username = username
        self.repository = repository
        self.tag = tag
        self.protocol = protocol

    def __str__(self):
        return f"{self.server}%{self.repository}%{self.tag}"

    @classmethod
    def FromUrl(cls, url: str, tag: str, type='git'):

        """
        Parse git server and repository name from url.
        This is expected to be the full address to the
        git repo according to either the ssh or https
        format.

        Raises:
            ValueError: url does not match pattern
        """

        git_addr = url
        good_patterns = ['git@{}:{}/{}.git', '{}://{}/{}/{}.git']
        parse_result_ssh = parse(good_patterns[0], git_addr)
        parse_result_https = parse(good_patterns[1], git_addr)

        if parse_result_ssh is not None:
            protocol = 'ssh'
            server, username, repository = parse_result_ssh
        elif parse_result_https is not None:
            protocol, server, username, repository = parse_result_https
        else:
            raise ValueError(f'could not parse git repository from given args {url}')

        return cls(server=server,
                   username=username,
                   repository=repository,
                   tag=tag,
                   protocol=protocol)


# class Recipe:
#     def __init__(self, name: str, source: RecipeSource, subdir='recipes'):
#         self.name = name
#         self.subdir = subdir
#         self.source = source
#
#     def __str__(self):
#         return f"{self.source}%{self.subdir}%{self.name}"


class Cookbook:
    basedir: str
    _recipes_dirname: str = 'recipes'

    @classmethod
    def set_recipe_basedir(cls, path):
        cls.basedir = path

    @classmethod
    def get_recipe_basedir(cls):
        """
        Returns the directory with recipes inside.
        """

        if cls.basedir is None:
            raise ValueError("Recipes' folder path missing")

        return cls.basedir

    @classmethod
    def get_recipe_path(cls):
        return _find_path_to_dir(cls.get_recipe_basedir(), cls._recipes_dirname)

    @classmethod
    def get_available_recipes(cls) -> typing.List[str]:
        """
        Returns a list of available recipe names
        """

        path = cls.get_recipe_path()

        if path is None:
            return []

        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        files = [os.path.splitext(f)[0] for f in files]
        files.sort()
        return files

    @classmethod
    def add_recipes(cls,
                    recipe_src: RecipeSource) -> bool:

        if os.path.exists(os.path.join(cls.get_recipe_basedir(), recipe_src.repository)):
            print(f'{recipe_src.repository}/{recipe_src.tag}: recipes source code already exists, skipping clone')
            print(f'if you want to update recipes sources (fetch/pull), you may do so using git\nin {cls.get_recipe_basedir()}')
            return False

        if os.listdir(cls.get_recipe_basedir()):
            print(f"recipes' repository already in '{cls.get_recipe_basedir()}':\nremove it if you want to add a different one")
            return False

        try:
            _clone_recipes_src(recipe_src, os.path.join(cls.get_recipe_basedir(), recipe_src.repository))

        except RuntimeError as e:
            print(e)
            return False

        return True


def _clone_recipes_src(recipe_src: RecipeSource, destination: str):
    # clone
    g = GitTools(destination)
    repo = os.path.join(recipe_src.username, recipe_src.repository) + '.git'
    if not g.clone(recipe_src.server, repo, tag=recipe_src.tag, proto=recipe_src.protocol):
        raise RuntimeError(f'{recipe_src}: recipes source code clone failed')

    print(f'{recipe_src.repository} ({recipe_src.tag}): recipes source code successfully cloned')


def _find_path_to_dir(basedir, dirname):
    for dirpath, dirs, files in os.walk(os.path.expanduser(basedir), followlinks=True):
        if dirname in dirs:
            return os.path.join(dirpath, dirname)
