from typing import List
import yaml
import os

class BasicPackage:
    def __init__(self, name, depends:List[str]=list()) -> None:
        self.name = name 
        self.depends = depends


class Package(BasicPackage):

    recipe_path = '../../recipes'

    def __init__(self, name, server, repository, tag=None, depends=list(), cmake_args=list()) -> None:
        super().__init__(name, depends)
        self.git_tag = tag
        self.git_server = server
        self.git_repo = repository
        self.cmake_args = cmake_args
        self.cmakelists = ''
        self.target = 'install'

    @staticmethod
    def from_yaml(name, yaml):
        if 'clone' in yaml.keys() and 'build' in yaml.keys():
            return Package(name=name, 
                server=yaml['clone']['server'],
                repository=yaml['clone']['repository'],
                tag=yaml['clone'].get('tag', None),
                depends=yaml.get('depends', list()),
                cmake_args=yaml['build'].get('args', list()))
        else:
            return BasicPackage(name=name, 
                depends=yaml['depends'])


    @staticmethod
    def from_file(file):
        name = os.path.splitext(os.path.basename(file))[0]
        with open(file, 'r') as f:
            yaml_dict = yaml.safe_load(f.read())
            return Package.from_yaml(name=name, yaml=yaml_dict)

    @staticmethod
    def from_name(name):
        this_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(this_dir, Package.recipe_path, name + '.yaml')
        if not os.path.exists(filename):
            raise RuntimeError(f'{filename} does not exist')
        return Package.from_file(file=filename)
