from typing import List
import yaml
import os

class BasicPackage:

    """Represent a package in its most basic form, i.e. a name
    and a list of dependencies
    """

    def __init__(self, name, depends:List[str]=None) -> None:
        self.name = name 
        self.depends = depends if depends is not None else list()


class Package(BasicPackage):

    """Represent a 'full' package, i.e. that can be cloned and built
    with git and cmake (for now that's all we support)
    """

    
    @staticmethod
    def get_recipe_path():
        """
        Returns the default (and for now only) directory with recipes inside.
        This path is relative to this file's directory.
        """
        this_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.realpath(os.path.join(this_dir, '../recipes'))

    @staticmethod
    def get_available_recipes() -> List[str]:
        """
        Returns a list of available recipe names
        """
        path = Package.get_recipe_path()
        files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        files = [os.path.splitext(f)[0] for f in files]
        files.sort()
        return files

    def __init__(self, name, server, repository, tag=None, depends=None, cmake_args=None, cmakelists='') -> None:
        super().__init__(name, depends)
        self.git_tag = tag
        self.git_server = server
        self.git_repo = repository
        self.cmake_args = cmake_args if cmake_args is not None else list()
        self.cmakelists = cmakelists
        self.target = 'install'


    @staticmethod
    def from_yaml(name, yaml):
        """
        Construct a Package or BasicPackage from yaml dict

        Args:
            name (str): the package name
            yaml (dict): a dictionary with package information

        Returns:
            Package: the constructed object
        """

        if 'clone' in yaml.keys() and 'build' in yaml.keys():
            return Package(name=name, 
                server=yaml['clone']['server'],
                repository=yaml['clone']['repository'],
                tag=yaml['clone'].get('tag', None),
                depends=yaml.get('depends', list()),
                cmake_args=yaml['build'].get('args', list()),
                cmakelists=yaml['build'].get('cmakelists', ''))
        else:
            return BasicPackage(name=name, 
                depends=yaml['depends'])


    @staticmethod
    def from_file(file):
        """
        Construct a Package or BasicPackage from file
        """

        name = os.path.splitext(os.path.basename(file))[0]
        with open(file, 'r') as f:
            yaml_dict = yaml.safe_load(f.read())
            return Package.from_yaml(name=name, yaml=yaml_dict)

    @staticmethod
    def from_name(name):
        """
        Construct a Package or BasicPackage from its name. The recipe file
        is first fetched from the default recipe path, and the returned
        object is constructed based on its content.

        Raises:
            RuntimeError: recipe file does not exist
        """

        filename = os.path.join(Package.get_recipe_path(), name + '.yaml')
        if not os.path.exists(filename):
            # TODO more specific exception
            raise FileNotFoundError(f'{filename} does not exist')
        return Package.from_file(file=filename)

