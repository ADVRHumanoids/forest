import shutil
import os
import typing
from tempfile import TemporaryDirectory
import yaml
import collections
from typing import List
from parse import parse
import re

from forest.common.package import Package
from forest.git_tools import GitTools
import forest.common.proc_utils as proc_utils
from forest.git_tools import *
# the file containing recipe repositories
recipe_fname = 'recipes.yaml'


# - clone repository (with given branch) into recipes/src
# - symlink all .yaml files from recipes/src/miao/foldername to recipes
# - handle conflicts, as follows
#   * in default mode, conflict is an error
#   * with --allow-recipe-overwrite, last file is used and an informative message is printed


class RecipeSource:
    def __init__(self, server: str, repository: str, tag: str):
        self.server = server
        self.repository = repository
        self.tag = tag

    def __str__(self):
        return f"{self.server}%{self.repository}%{self.tag}"


class Recipe:
    def __init__(self, name: str, source: RecipeSource, subdir='recipes'):
        self.name = name
        self.subdir = subdir
        self.source = source


class Cookbook:
    recipes_basedir: str
    recipes: typing.Mapping[str, typing.Sequence[str]]

    @classmethod
    def add_recipes(cls, *recipes: str, recipe_src: RecipeSource, recipes_subfolder: str = 'recipes'):
        # 1. clone recipes
        # 2. symlink recipes
        # 3. update cls.recipes
        _clone_recipes(cls.recipes_basedir, recipe_src, recipes_subfolder, recipes)

    @classmethod
    def _update(cls):
        # 1. check self.recipes_basedir for recipes
        # 2. get symlinks's real paths os.path.realpath
        # 3. update cls.recipes

class UserInterrupt(Exception):
    pass


def _clone_recipes(recipes_basedir: str,
                  recipe_src: RecipeSource,
                  recipes_subfolder: str,
                  recipes: typing.Optional[typing.Sequence[str]] = None) -> bool:

    destination_basefolder = os.path.join(recipes_basedir, 'src')
    destination_folder = os.path.join(destination_basefolder, recipe_src.repository, recipe_src.tag)
    if os.path.exists(destination_folder):
        print(f'{recipe_src.repository}/{recipe_src.tag}: recipes source code  already exists, skipping clone')
        print(f'if you want to update recipes sources fetch/pull you may do so using git in {destination_folder}')

    else:
        g = GitTools(destination_folder)
        if not g.clone(recipe_src.server, recipe_src.repository, branch=recipe_src.tag, single_branch=True):
            return False

        print(f'{recipe_src.repository}/{recipe_src.tag}: cloned recipes source code')

    recipes_folder = os.path.join(destination_folder, recipes_subfolder)

    duplicates = duplicate_recipes(recipes, recipes_basedir)
    if duplicates:
        # todo: add overwrite policy for unattended usage
        # todo: add possibility to choose which symlink for attended usage
        raise ValueError(f'trying to add duplicates of local recipes: {duplicates}\naborting symlink...')

    for r in recipes:
        symlink(r, from_folder=recipes_folder, to_folder=recipes_basedir)


def symlink(recipe_fname: str, from_folder: str, to_folder: str) -> bool:
    if not re.search("\.yaml$", recipe_fname):
        raise ValueError(f'recipe_fname: {recipe_fname} must have .yaml extension')
    cmd = ['ln', '-s', os.path.join(from_folder, recipe_fname), os.path.join(to_folder, recipe_fname)]
    return proc_utils.call_process(cmd)


def duplicate_recipes(incoming_recipes: typing.Sequence[str], recipe_folder: str) -> typing.Set[str]:
    set_of_incoming_recipes = set(incoming_recipes)
    assert len(incoming_recipes) == len(set_of_incoming_recipes)   # no duplicate in incoming recipes
    current_recipes = filenames_from_folder(recipe_folder)
    return set_of_incoming_recipes & current_recipes


def filenames_from_folder(folder: str) -> typing.Set[str]:
    return set(f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)))



class Cookbook:
    def __init__(self, path):
        self.path = path
        self.recipes: typing.Mapping[str, Recipe] = {}

    def add_recipe(self):
        pass


class CookBook:
    recipe_fname = None
    
    def __init__(self):
        with open(self.recipe_fname, 'r') as f:
            yaml_list = yaml.safe_load(f.read())
            if yaml_list is None:
                yaml_list = list()

        self.sources = []
        for el in yaml_list:
            self.sources.append(RecipeSource(el['type'], el["server"], el["repository"], el["tag"]))

        self.recipes = {}

    @classmethod
    def write_recipe_file(cls, rootdir, recipe_fname='recipes.yaml'):
        """
        Write a hidden file to store info where to find recipes
        """

        fname = os.path.join(rootdir, recipe_fname)
        cls.recipe_fname = fname
        if os.path.exists(fname):
            return True

        with open(fname, 'w') as f:
            f.write('# recipes info file')
            return True

    @classmethod
    def add_recipes_source(cls, entry: List[str]):
        _type = 'git'

        with open(cls.recipe_fname, 'r') as f:
            yaml_list = yaml.safe_load(f.read())
            if yaml_list is None:
                yaml_list = list()

            if not cls._add_source_to_yaml(entry, yaml_list):
                return False

        with open(cls.recipe_fname, 'w') as f:
            yaml.dump(data=yaml_list, stream=f)
            return True

    @classmethod
    def _add_source_to_yaml(cls, entry: List[str], yaml_list) -> bool:
        _type = 'git'
        server, name, tag = cls._parse_entry(entry, type=_type)

        entry = {
            'type': _type,
            'server': server,
            'repository': name,
            'tag': tag
        }

        for yaml_entry in yaml_list:
            if all(entry[field] == yaml_entry[field] for field in ('repository', 'tag', 'server')):
                print(f'Entry {entry["repository"]} @{entry["tag"]} already exists')
                return False

        yaml_list.append(entry)
        return True

    def add_recipe_src(self, entry: List[str]):
        _type = 'git'
        server, name, tag = self._parse_entry(entry, type=_type)
        recipe_src = RecipeSource(_type, server, name, tag)
        if not self._check_recipe_source(recipe_src):
            print(f'Invalid recipe source: {recipe_src}')
            return False
        if not self.add_recipes_source(entry):
            print(f'Recipe source {recipe_src} already present')

        else:
            print(f'Added recipe source: {recipe_src}')

        return True

    def _check_recipe_source(self, recipe_src: RecipeSource):
        # todo: check that recipe_src is a valid source, return False otherwise
        return True

    @staticmethod
    def _parse_entry(entry: List[str], type='git'):

        """
        Parse git server and repository name from the first element
        of the input list (entry[0]). This is expected to be the
        full address to the git repo according to either the ssh or
        https format.


        Raises:
            ValueError: entry[0] does not match mattern

        Returns:
            str, str: server and repository
        """

        git_addr = entry[0]
        git_tag = entry[1]
        good_patterns = ['git@{}:{}/{}.git', 'https://{}/{}/{}.git']
        parse_result_ssh = parse(good_patterns[0], git_addr)
        parse_result_https = parse(good_patterns[1], git_addr)

        if parse_result_ssh is not None:
            server, username, repository = parse_result_ssh
        elif parse_result_https is not None:
            server, username, repository = parse_result_https
        else:
            raise ValueError(f'could not parse git repository from given args {entry}')

        return server, f'{username.lower()}/{repository.lower()}.git', git_tag

    def _fetch_recipes(self, source: RecipeSource, path_to_recipes_dir='recipes'):
        """
        Fetch recipes from source and store them in a temporary directory.

        Return TemporaryDirectory object that manages the temporary directory
        where the recipes have been stored. To delete the temporary dir call the
        cleanup method on the TemporaryDirectory object.
        """

        tmpdir = TemporaryDirectory(prefix="forest-")

        git_tools = GitTools(tmpdir.name)

        # git clone proto
        from forest.common.fetch_handler import GitFetcher
        proto = GitFetcher.proto_override
        if proto is None:
            proto = 'ssh'

        # git clone
        if not git_tools.clone(source.server, source.repository, proto=proto):
            return []

        # git checkout
        if not git_tools.checkout(source.tag):
            return []

        # recipes are taken from the recipes/ subfolder
        recipe_dir = os.path.join(tmpdir.name, path_to_recipes_dir)
        recipes = sorted(f for f in os.listdir(recipe_dir) if os.path.isfile(os.path.join(recipe_dir, f)))
        self.recipes[str(source)] = {}
        for recipe in recipes:
            name = os.path.split(recipe)[1]
            self.recipes[str(source)][name] = Recipe(name, source, os.path.join(recipe_dir, recipe))

        return tmpdir

    def _map_recipe_to_sources(self) -> dict:
        """
        Return a dictionary that maps each recipe to all its possible sources
        """

        # get set of all recipes in the remotes
        recipe_names = set().union(*[d for d in self.recipes.values()])

        # create a dict recipe: list of sources
        recipe_to_sources = {}
        for recipe in recipe_names:
            recipe_to_sources[recipe] = []
            for name, source in self.recipes.items():
                if recipe in source:
                    recipe_to_sources[recipe].append(name)

        return recipe_to_sources

    def _select_sources(self, recipe_to_sources: dict) -> dict:
        """
        Prompt the user to select one source among the possible ones
        for all those recipes with multiple sources
        """

        intro_txt = 'CONFLICT select a source for recipe  {}  among:'
        quit_text = 'or digit "q" to QUIT forest\n'
        for recipe, sources in recipe_to_sources.items():
            prompt_txt = '\n'.join(
                [intro_txt.format(os.path.splitext(recipe)[0])]
                + ['\t{}: {}'.format(idx, source) for idx, source in enumerate(sources)]
                + [quit_text])
            selected = False
            if len(sources) > 1:
                while not selected:
                    src_id = input(prompt_txt)
                    if src_id == 'q':
                        raise UserInterrupt

                    else:
                        try:
                            if 0 <= int(src_id) < len(sources):
                                recipe_to_sources[recipe] = [sources[int(src_id)]]
                                selected = True

                            else:
                                print(f'INVALID INPUT: index {int(src_id)} is out of range\n')

                        except ValueError:
                            print('INVALID INPUT\n')

    def update_recipes(self, recipes=None, path_to_recipes_dir='recipes'):
        tmpdirs = []
        for source in self.sources:
            tmpdirs.append(self._fetch_recipes(source, path_to_recipes_dir))

        recipe_to_sources = self._map_recipe_to_sources()

        if recipes is not None:
            try:
                recipe_to_sources = {f'{recipe}.yaml': recipe_to_sources[f'{recipe}.yaml'] for recipe in recipes}

            except KeyError as e:
                print(f'Invalid recipe name: {os.path.splitext(e.args[0])[0]}')
                return False

        try:
            self._select_sources(recipe_to_sources)

        except UserInterrupt:
            # the user wants to quit halfway through the selection of sources
            # delete the temporary dirs where the recipes where stored during the fetch
            print('Recipes not updated')
            tmpdirs.clear()
            return False

        for recipe, sources in recipe_to_sources.items():
            assert len(sources) == 1
            recipe_name = os.path.splitext(recipe)[0]

            if recipe_name in Package.get_available_recipes():
                print(f'[{recipe_name}] updating recipe from {sources[0]}')

            else:
                print(f'[{recipe_name}] adding recipe from {sources[0]}')

            shutil.copy(self.recipes[str(sources[0])][recipe].full_path, Package.get_recipe_path())

        # delete the temporary dirs where the recipes where stored during the fetch
        tmpdirs.clear()
        return True










