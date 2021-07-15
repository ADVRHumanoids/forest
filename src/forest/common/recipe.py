import shutil
import os
from tempfile import TemporaryDirectory
import yaml
import collections
from typing import List

from forest.common.package import Package
from forest.git_tools import GitTools


recipe_fname = 'recipes.yaml'

def add_recipe_repository(entries : List[str]):

    keys = ['type', 'server', 'repository', 'tag']
    entry = dict(zip(keys, entries))

    with open(recipe_fname, 'r') as f:
        yaml_dict = yaml.safe_load(f.read())
        if yaml_dict is None:
            yaml_dict = list()
        yaml_dict.append(entry)
    
    with open(recipe_fname, 'w') as f:
        yaml.dump(data=yaml_dict, stream=f)


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
        # git clone
        git_tools = GitTools(tmpdir)
        git_tools.clone(server, repository, proto='ssh')
        git_tools.checkout(tag)
        
        recipe_dir = os.path.join(tmpdir, 'recipes')
        recipes = add_recipes(recipe_dir)

    return recipes


def add_recipes(recipe_dir_path):
    recipes = []
    files = {f for f in os.listdir(recipe_dir_path) if os.path.isfile(os.path.join(recipe_dir_path, f))}
    for f in files:
        recipe_name = os.path.splitext(f)[0]
        if recipe_name in Package.get_available_recipes():
            print(f'[{recipe_name}] Updating recipe in {Package.get_recipe_path()}')

        else:
            print(f'[{recipe_name}] Adding recipe to {Package.get_recipe_path()}')

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
