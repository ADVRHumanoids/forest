
import os
import re

from forest.git_tools import *
from parse import parse
# - clone repository (with given branch) into recipes/src
# - symlink all .yaml files from recipes/src/repo/tag/subdir to recipes
# - handle conflicts, as follows
#   * in default mode, choose which source to keep
#   * with --allow-recipe-overwrite, last file is used and an informative message is printed


class DuplicateRecipes(Exception):
    pass


class UserInterrupt(Exception):
    pass


class RecipeSource:
    def __init__(self, server: str, username: str, repository: str, tag: str):
        self.server = server
        self.username = username
        self.repository = repository
        self.tag = tag

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
        good_patterns = ['git@{}:{}/{}.git', 'https://{}/{}/{}.git']
        parse_result_ssh = parse(good_patterns[0], git_addr)
        parse_result_https = parse(good_patterns[1], git_addr)

        if parse_result_ssh is not None:
            server, username, repository = parse_result_ssh
        elif parse_result_https is not None:
            server, username, repository = parse_result_https
        else:
            raise ValueError(f'could not parse git repository from given args {url}')

        return cls(server, username, repository, tag)


class Recipe:
    def __init__(self, name: str, source: RecipeSource, subdir='recipes'):
        self.name = name
        self.subdir = subdir
        self.source = source

    def __str__(self):
        return f"{self.source}%{self.subdir}%{self.name}"


class Cookbook:
    basedir: str
    recipes_src_subdir: str = 'src'
    recipes: typing.Mapping[str, str]

    @classmethod
    def add_recipes(cls,
                    recipe_src: RecipeSource,
                    recipes: typing.Optional[typing.Sequence[str]] = None,
                    subdir: str = 'recipes',
                    allow_overwrite: bool = False) -> None:

        # 0. update cls.recipes
        cls.update()

        # 1. clone recipes' src
        destination_basedir = os.path.join(cls.basedir, cls.recipes_src_subdir)
        destination_dir = os.path.join(destination_basedir, recipe_src.repository, recipe_src.tag)
        _clone_recipes_src(recipe_src, destination_dir)

        # 2. check for duplicate recipes
        recipes_dir = os.path.join(destination_dir, subdir)
        recipes_with_ext = [r + '.yaml' if not _has_yaml_ext(r) else r for r in recipes]

        if not recipes_with_ext:
            # empty recipes -> add all recipes
            recipes_with_ext = _filenames_from_folder(recipes_dir)

        duplicates = _duplicate_recipes(recipes_with_ext, cls.basedir)
        if duplicates and not allow_overwrite:
            recipes_with_ext = _select_recipes(cls.basedir, recipes_dir, recipes_with_ext, duplicates)

        # 3. symlink recipes
        for r in recipes_with_ext:
            _symlink(r, file_folder=recipes_dir, link_folder=cls.basedir)

        # 3. update cls.recipes
        cls.update()

    @classmethod
    def remove_recipes(cls, recipes: typing.Optional[typing.Sequence[str]] = None) -> None:
        # todo: if no links to source, remove source ? Maybe optional bool parameter remove_source

        # 0. update cls.recipes
        cls.update()

        if not recipes:
            # empty recipes -> remove all recipes
            recipes = _filenames_from_folder(cls.basedir)

        # 1. remove symlink
        for r in recipes:
            if not _has_yaml_ext(r):
                r += '.yaml'
                os.remove(os.path.join(cls.basedir, r))

        # 2. update cls.recipes
        cls.update()

    @classmethod
    def update(cls):
        # 1. check cls.basedir for recipes
        recipes = _filenames_from_folder(cls.basedir)

        # 2. update cls.recipes
        cls.recipes = {r: os.path.realpath(r) for r in recipes}


def _clone_recipes_src(recipe_src: RecipeSource, destination: str) -> bool:

    if os.path.exists(destination):
        print(f'{recipe_src.repository}/{recipe_src.tag}: recipes source code already exists, skipping clone')
        print(f'if you want to update recipes sources (fetch/pull), you may do so using git\nin {destination}')
        return False

    else:
        g = GitTools(destination)
        repo = os.path.join(recipe_src.username, recipe_src.repository) + '.git'
        if not g.clone(recipe_src.server, repo, branch=recipe_src.tag, single_branch=True):
            raise RuntimeError(f'{recipe_src}: recipes source code clone failed')

        print(f'{recipe_src.repository}/{recipe_src.tag}: recipes source code successfully cloned')
        return True


def _symlink(recipe_fname: str, file_folder: str, link_folder: str) -> bool:
    if not _has_yaml_ext(recipe_fname):
        raise ValueError(f'recipe_fname: {recipe_fname} must have .yaml extension')
    cmd = ['ln', '-fs', os.path.join(file_folder, recipe_fname), os.path.join(link_folder, recipe_fname)]
    return proc_utils.call_process(cmd)


def _has_yaml_ext(fname):
    return re.search("\.yaml$", fname)


def _duplicate_recipes(incoming_recipes: typing.Sequence[str], recipe_folder: str) -> typing.Set[str]:
    set_of_incoming_recipes = set(incoming_recipes)
    assert len(incoming_recipes) == len(set_of_incoming_recipes)   # no duplicate in incoming recipes
    current_recipes = _filenames_from_folder(recipe_folder)
    return set_of_incoming_recipes & current_recipes


def _filenames_from_folder(folder: str) -> typing.Set[str]:
    return set(f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)))


def _select_recipes(cookbook_basedir, recipes_dir, new_recipes, duplicates) -> typing.Set[str]:
    """
    return the ones to be removed from recipes
    """

    selected_recipes = new_recipes.copy()
    for d in duplicates:
        current_src = os.path.realpath(os.path.join(cookbook_basedir, d))
        new_src = os.path.join(recipes_dir, d)
        if not current_src == new_src:
            source = _select_source(d, [current_src, new_src])

            if source == current_src:
                selected_recipes.remove(d)

    return selected_recipes


def _select_source(recipe: str, sources: typing.Sequence[str]) -> str:

    """
    Prompt the user to select one source among the possible ones
    for all those recipes with multiple sources
    """

    assert len(sources) > 1
    intro_txt = 'CONFLICT select a source for recipe  {}  among:'
    quit_text = 'or digit "q" to QUIT forest\n'

    prompt_txt = '\n'.join(
        [intro_txt.format(os.path.splitext(recipe)[0])]
        + ['\t{}: {}'.format(idx, source) for idx, source in enumerate(sources)]
        + [quit_text])

    while True:
        src_id = input(prompt_txt)
        if src_id == 'q':
            raise UserInterrupt

        else:
            try:
                if 0 <= int(src_id) < len(sources):
                    return sources[int(src_id)]

                else:
                    print(f'INVALID INPUT: index {int(src_id)} is out of range\n')

            except ValueError:
                print('INVALID INPUT\n')










