import shutil
import os
from tempfile import TemporaryDirectory
import yaml
import collections
from typing import List
from parse import parse

from forest.common.package import Package
from forest.git_tools import GitTools

# the file containing recipe repositories
recipe_fname = 'recipes.yaml'


class CookBook(object):
    recipe_fname = None

    @classmethod
    def set_recipe_fname(cls, rootdir, recipe_fname='recipes.yaml'):
        """
        Write a hidden file to store info where to find recipes
        """

        fname = os.path.join(rootdir, recipe_fname)
        cls.recipe_fname = fname
        if os.path.exists(fname):
            return False

        with open(fname, 'w') as f:
            f.write('# recipes info file')
            return True

    @classmethod
    def add_recipes_source(cls, entries : List[str]):
        _type='git'
        server, name, tag = cls._parse_entries(entries, type=_type)

        with open(cls.recipe_fname, 'r') as f:
            yaml_list = yaml.safe_load(f.read())
            if yaml_list is None:
                yaml_list = list()

            if not cls._add_source_to_yaml(entries, yaml_list):
                return False

        with open(cls.recipe_fname, 'w') as f:
            yaml.dump(data=yaml_list, stream=f)
            return True

    @classmethod
    def _add_source_to_yaml(cls, entry: dict, yaml_list) -> bool:
        _type = 'git'
        server, name, tag = cls._parse_entries(entry, type=_type)

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

    @classmethod
    def add_recipes(cls, entries : List[str]):
        if not cls.add_recipes_source(entries):
            print('skip add recipes...')

        else:
            # add recipes only first time a new source is added
            _type = 'git'
            server, name, tag = cls._parse_entries(entries, type=_type)
            with TemporaryDirectory(prefix="forest-") as recipes_tmpdir:
                recipes = cls._fetch_recipes(server, name, tag, recipes_tmpdir)

                check_recipes = recipes.copy()
                check_recipes.extend(Package.get_available_recipes())
                if len(check_recipes) != len(set(check_recipes)):
                    duplicates = [item for item, count in collections.Counter(check_recipes).items() if count > 1]
                    raise ValueError(f'Trying to add duplicates of the same recipe: {duplicates}')  # todo: meaningful error

                for recipe in recipes:
                    # recipe_name = os.path.splitext(f)[0]
                    if recipe in Package.get_available_recipes():
                        print(f'[{recipe}] updating recipe in {Package.get_recipe_path()}')

                    else:
                        print(f'[{recipe}] adding recipe to {Package.get_recipe_path()}')

                    shutil.copy(os.path.join(recipes_tmpdir, 'recipes', f'{recipe}.yaml'), Package.get_recipe_path())

        return True

    @staticmethod
    def _parse_entries(entries : List[str], type='git'):

        """
        Parse git server and repository name from the first element
        of the input list (entries[0]). This is expected to be the
        full address to the git repo according to either the ssh or
        https format.


        Raises:
            ValueError: entries[0] does not match mattern

        Returns:
            str, str: server and repository
        """

        git_addr = entries[0]
        git_tag = entries[1]
        good_patterns = ['git@{}:{}/{}.git', 'https://{}/{}/{}.git']
        parse_result_ssh = parse(good_patterns[0], git_addr)
        parse_result_https = parse(good_patterns[1], git_addr)

        if parse_result_ssh is not None:
            server, username, repository = parse_result_ssh
        elif parse_result_https is not None:
            server, username, repository = parse_result_https
        else:
            raise ValueError(f'could not parse git repository from given args {entries}')

        return server, f'{username.lower()}/{repository.lower()}.git', git_tag

    @staticmethod
    def _fetch_recipes(server, repository, tag, tmpdir):
        """address: 'GIT {server}:{repository} TAG """

        # with TemporaryDirectory(prefix="forest-") as tmpdir:

        git_tools = GitTools(tmpdir)

        # git clone proto
        from forest.common.fetch_handler import GitFetcher
        proto = GitFetcher.proto_override
        if proto is None:
            proto = 'ssh'
        
        # git clone
        if not git_tools.clone(server, repository, tag, proto=proto):
            return []

        # recipes are taken from the recipes/ subfolder
        recipe_dir = os.path.join(tmpdir, 'recipes')
        recipes = [os.path.splitext(f)[0] for f in os.listdir(recipe_dir) if
                   os.path.isfile(os.path.join(recipe_dir, f))]
        recipes.sort()
        return recipes

    @classmethod
    def update_recipes(cls):
        with open(cls.recipe_fname, 'r') as f:
            yaml_list = yaml.safe_load(f.read())
            if yaml_list is None:
                yaml_list = list()

        recipes_cache = []

        for source in yaml_list:
            if source['type'].lower() == 'git':
                with TemporaryDirectory(prefix="forest-") as recipes_tmpdir:
                    try:
                        print(f'Fetching recipes from {source["server"]}: {source["repository"]} @{source["tag"]}')
                        recipes = cls._fetch_recipes(source['server'], source['repository'], source['tag'], recipes_tmpdir)

                    except KeyError as e:
                        raise KeyError(f'recipes.yaml git entry is missing {e.args[0]} mandatory key')

                    # check for duplicates
                    recipes_cache.extend(recipes)
                    if len(recipes_cache) != len(set(recipes_cache)):
                        duplicates = [item for item, count in collections.Counter(recipes_cache).items() if count > 1]
                        print(f'Trying to fetch duplicates of the same recipe: {duplicates}')
                        print('UPDATE FAILED')
                        return False

                    for recipe in recipes:
                        print(f'Updating {recipe}')
                        shutil.copy(os.path.join(recipes_tmpdir, 'recipes', f'{recipe}.yaml'), Package.get_recipe_path())

            else:
                raise TypeError(f'Not supported type {source["type"]} for fetching recipes')

        return True