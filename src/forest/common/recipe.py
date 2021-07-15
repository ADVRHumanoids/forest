import shutil
import os
from tempfile import TemporaryDirectory
import typing
import yaml
import collections
from typing import List
from parse import parse
import sys

from forest.common.package import Package
from forest.git_tools import GitTools


recipe_fname = 'recipes.yaml'

def parse_git_repository(entries : List[str]):

    gitaddr = entries[0]
    type = 'git'
    good_patterns = ['git@{}:{}.git', 'https://{}/{}.git']
    parse_result_ssh = parse(good_patterns[0], entries[0])
    parse_result_https = parse(good_patterns[1], entries[0])

    if parse_result_ssh is not None:
        server, repository = parse_result_ssh
    elif parse_result_https is not None:
        server, repository = parse_result_https
    else:
        raise ValueError(f'could not parse git repository from given args {entries}')

    return server, repository

def add_recipe_repository(entries : List[str]):

    # for now, we only support git
    gitaddr = entries[0]
    type = 'git'
    server, repository = parse_git_repository(entries)

    entry = {
        'type': type,
        'server': server, 
        'repository': repository + '.git',
        'tag': entries[1]
    }

    with open(recipe_fname, 'r') as f:
        yaml_dict = yaml.safe_load(f.read())
        if yaml_dict is None:
            yaml_dict = list()
        yaml_dict.append(entry)
    
    with open(recipe_fname, 'w') as f:
        yaml.dump(data=yaml_dict, stream=f)

    return True


def fetch_recipes_from_file(path):
    
    with open(path, 'r') as f:
        yaml_dict = yaml.safe_load(f.read())

    fetch_recipes_from_yaml(yaml_dict)
    return True


def fetch_recipes_from_yaml(yaml):
    recipes_cache = []
    for source in yaml:
        if source['type'].lower() == 'git':
            try:
                print(f'Fetching recipes from {source["server"]}: {source["repository"]} @{source["tag"]}')
                recipes = fetch_recipes_from_git(source['server'], source['repository'], source['tag'])

                # check for duplicates
                recipes_cache.extend(recipes)
                if len(recipes_cache) != len(set(recipes_cache)):
                    duplicates = [item for item, count in collections.Counter(recipes_cache).items() if count > 1]
                    raise ValueError(f'Trying to fetch duplicates of the same recipe: {duplicates}')   # todo: create DuplicateRecipeError

            except KeyError as e:
                raise KeyError(f'recipes.yaml git entry is missing {e.args[0]} mandatory key')

        else:
            raise TypeError(f'Not supported type {source["type"]} for fetching recipes')


def fetch_recipes_from_git(server, repository, tag):

    """address: 'GIT {server}:{repository} TAG """

    with TemporaryDirectory(prefix="forest-") as tmpdir:
        
        git_tools = GitTools(tmpdir)

        # git clone
        if not git_tools.clone(server, repository, proto='ssh'):
            return []

        # git checkout
        if not git_tools.checkout(tag):
            return []
        
        # recipes are taken from the recipes/ subfolder
        recipe_dir = os.path.join(tmpdir, 'recipes')
        return add_recipes(recipe_dir)


def add_recipes(recipe_dir_path):
    recipes = []
    files = {f for f in os.listdir(recipe_dir_path) if os.path.isfile(os.path.join(recipe_dir_path, f))}
    for f in files:
        recipe_name = os.path.splitext(f)[0]
        if recipe_name in Package.get_available_recipes():
            print(f'[{recipe_name}] updating recipe in {Package.get_recipe_path()}')

        else:
            print(f'[{recipe_name}] adding recipe to {Package.get_recipe_path()}')

        shutil.copy(os.path.join(recipe_dir_path, f), Package.get_recipe_path())
        recipes.append(recipe_name)

    return recipes


def write_recipes_yaml_file(rootdir):

    """
    Write a hidden file to store info where to find recipes
    """

    if os.path.exists(recipe_fname):
        return False

    with open(recipe_fname, 'w') as f:
        f.write('# recipes info file')
        return True
