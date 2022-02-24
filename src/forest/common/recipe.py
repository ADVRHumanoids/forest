
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
    recipes_src_subdir: str = 'src'
    recipes: typing.Mapping[str, str]

    @classmethod
    def set_recipe_path(cls, path):
        cls.basedir = path

    @classmethod
    def get_recipe_path(cls):
        """
        Returns the directory with recipes inside.
        """

        if cls.basedir is None:
            raise ValueError("Recipes' folder path missing")

        return cls.basedir

    @classmethod
    def get_available_recipes(cls) -> typing.List[str]:
        """
        Returns a list of available recipe names
        """
        path = cls.get_recipe_path()
        if not os.path.isdir(path):
            return []

        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        files = [os.path.splitext(f)[0] for f in files]
        files.sort()
        return files

    @classmethod
    def add_recipes(cls,
                    recipe_src: RecipeSource,
                    recipes: typing.Optional[typing.Sequence[str]] = None,
                    subdir: str = 'recipes',
                    allow_overwrite: bool = False) -> bool:

        if recipes is None:
            recipes = []

        # 0. update cls.recipes
        cls.update()

        # 1. clone recipes' src
        destination_basedir = os.path.join(cls.get_recipe_path(), cls.recipes_src_subdir)
        destination_dir = os.path.join(destination_basedir, recipe_src.repository, recipe_src.tag)

        try:
            _clone_recipes_src(recipe_src, destination_dir)

        except RuntimeError as e:
            print(e)
            return False

        # 2. check for duplicate recipes
        recipes_dir = os.path.join(destination_dir, subdir)
        recipes_with_ext = [r + '.yaml' if not _has_yaml_ext(r) else r for r in recipes]

        if not recipes_with_ext:
            # empty recipes -> add all recipes
            recipes_with_ext = _filenames_from_folder(recipes_dir)

        duplicates = cls._duplicate_recipes(recipes_with_ext)
        if duplicates and not allow_overwrite:
            try:
                recipes_with_ext = cls._select_recipes(recipes_dir, recipes_with_ext, duplicates)

            except UserInterrupt:
                return False

        # 3. symlink recipes
        for r in recipes_with_ext:
            _symlink_recipe(r, file_folder=recipes_dir, link_folder=cls.get_recipe_path())

        # 3. update cls.recipes
        cls.update()

        return True

    @classmethod
    def remove_recipes(cls, recipes: typing.Optional[typing.Sequence[str]] = None) -> None:
        # todo: if no links to source, remove source ? Maybe optional bool parameter remove_source

        # 0. update cls.recipes
        cls.update()

        if not recipes:
            # empty recipes -> remove all recipes
            recipes = _filenames_from_folder(cls.get_recipe_path())

        # 1. remove symlink
        for r in recipes:
            if not _has_yaml_ext(r):
                r += '.yaml'
                os.remove(os.path.join(cls.get_recipe_path(), r))

        # 2. update cls.recipes
        cls.update()

    @classmethod
    def update(cls):
        # 1. check cls.basedir for recipes
        recipes = _filenames_from_folder(cls.get_recipe_path())

        # 2. update cls.recipes
        cls.recipes = {r: os.path.realpath(r) for r in recipes}

    @classmethod
    def _duplicate_recipes(cls, incoming_recipes: typing.Sequence[str]) -> typing.Set[str]:
        set_of_incoming_recipes = set(incoming_recipes)
        assert len(incoming_recipes) == len(set_of_incoming_recipes)  # no duplicate in incoming recipes
        current_recipes = _filenames_from_folder(cls.get_recipe_path())
        return set_of_incoming_recipes & current_recipes


    @classmethod
    def _select_recipes(cls, recipes_dir, new_recipes, duplicates) -> typing.Set[str]:
        """
        return the ones to be removed from recipes
        """

        selected_recipes = new_recipes.copy()
        for d in duplicates:
            current_src = os.path.realpath(os.path.join(cls.get_recipe_path(), d))
            new_src = os.path.join(recipes_dir, d)
            if not current_src == new_src:

                # strip base dir from sources path
                sources = [os.path.relpath(src, os.path.join(cls.get_recipe_path(), cls.recipes_src_subdir))
                           for src in [current_src, new_src]]
                source = cls._select_source(d, sources)

                if source == current_src:
                    selected_recipes.remove(d)

        return selected_recipes

    @classmethod
    def _select_source(cls, recipe: str, sources: typing.Sequence[str]) -> str:

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


def _clone_recipes_src(recipe_src: RecipeSource, destination: str) -> bool:

    if os.path.exists(destination):
        print(f'{recipe_src.repository}/{recipe_src.tag}: recipes source code already exists, skipping clone')
        print(f'if you want to update recipes sources (fetch/pull), you may do so using git\nin {destination}')
        return False

    else:
        # git clone proto (we take it from git fetcher)
        from forest.common.fetch_handler import GitFetcher
        proto = GitFetcher.proto_override
        if proto is None:
            proto = 'ssh'
        
        # clone
        g = GitTools(destination)
        repo = os.path.join(recipe_src.username, recipe_src.repository) + '.git'
        if not g.clone(recipe_src.server, repo, tag=recipe_src.tag, single_branch=True, proto=proto):
            raise RuntimeError(f'{recipe_src}: recipes source code clone failed')

        print(f'{recipe_src.repository}/{recipe_src.tag}: recipes source code successfully cloned')
        return True


def _symlink_recipe(recipe_fname: str, file_folder: str, link_folder: str) -> bool:
    if not _has_yaml_ext(recipe_fname):
        raise ValueError(f'recipe_fname: {recipe_fname} must have .yaml extension')
    
    symlink_src = os.path.join(file_folder, recipe_fname)
    symlink_dst = os.path.join(link_folder, recipe_fname)
    
    dst_exists = os.path.exists(symlink_dst)
    verb = 'updating' if dst_exists else 'adding'
    print(f'{verb} recipe {recipe_fname}')
    
    cmd = ['ln', '-fs', symlink_src, symlink_dst]
    return proc_utils.call_process(cmd)


def _has_yaml_ext(fname):
    return re.search("\.yaml$", fname)


def _filenames_from_folder(folder: str) -> typing.Set[str]:
    return set(f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)))
