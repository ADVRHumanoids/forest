from typing import List
import yaml
import os

from .fetch_handler import FetchHandler
from .build_handler import BuildHandler
from forest.common.eval_handler import EvalHandler
from forest.common.recipe import Cookbook


class BasicPackage:

    """
    Represent a package in its most basic form, i.e. a name
    and a list of dependencies
    """

    def __init__(self, name, depends: List[str]=None) -> None:
        self.name = name 
        self.depends = depends if depends is not None else list()
        

class Package(BasicPackage):

    """
    Represent a 'full' package, i.e. that can be cloned and built
    with git and cmake (for now that's all we support)
    """
    
    # the path to the recipe directory
    _path = None

    def __init__(self, name, depends: List[str]) -> None:
        super().__init__(name, depends=depends)
        self.fetcher = FetchHandler(name)
        self.builder = BuildHandler(name)

    @staticmethod
    def from_yaml(name, recipe) -> 'Package':
        """
        Construct a Package or BasicPackage from yaml dict

        Args:
            name (str): the package name
            recipe (dict): a dictionary with package information

        Returns:
            Package: the constructed object
        """

        # eval handler
        eh = EvalHandler.instance()

        # dependency list if any
        depends = recipe.get('depends', list())
        if depends is None:
            # empty entry "depends:" in yaml is parsed as None
            depends = list()
        depends_if = recipe.get('depends_if', dict())
        depends.extend(eh.parse_conditional_dict(depends_if))

        # create pkg
        pkg = Package(name=name, depends=depends)

        # custom fetcher and builder if we have clone/build information
        if 'clone' in recipe.keys():
            pkg.fetcher = FetchHandler.from_yaml(pkgname=name, data=recipe['clone'], recipe=recipe)

        if 'build' in recipe.keys():
            pkg.builder = BuildHandler.from_yaml(pkgname=name, data=recipe['build'], recipe=recipe)

        return pkg

    @staticmethod
    def from_file(file) -> 'Package':
        """
        Construct a Package or BasicPackage from file
        """

        name = os.path.splitext(os.path.basename(file))[0]
        with open(file, 'r') as f:
            yaml_dict = yaml.safe_load(f.read())
            if yaml_dict is None:
                yaml_dict = dict()
            return Package.from_yaml(name=name, recipe=yaml_dict)

    @staticmethod
    def from_name(name) -> 'Package':
        """
        Construct a Package or BasicPackage from its name. The recipe file
        is first fetched from the default recipe path, and the returned
        object is constructed based on its content.

        Raises:
            RuntimeError: recipe file does not exist
        """

        filename = os.path.join(Cookbook.get_recipe_path(), name + '.yaml')
        if not os.path.exists(filename):
            # TODO more specific exception
            raise FileNotFoundError(f'{filename} does not exist')
        return Package.from_file(file=filename)

