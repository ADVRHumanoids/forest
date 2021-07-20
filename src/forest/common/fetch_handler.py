from abc import ABC, abstractmethod
import os 
import getpass 

from forest.git_tools import GitTools
from . import proc_utils

class FetchHandler(ABC):

    def __init__(self, pkgname) -> None:
        self.pkgname = pkgname

    @abstractmethod
    def fetch(self, srcdir):
        pass 

    @classmethod
    def from_yaml(cls, pkgname, data):
        fetchtype = data['type']
        if fetchtype == 'git':
            return GitFetcher.from_yaml(pkgname=pkgname, data=data)
        elif fetchtype == 'deb':
            return DebFetcher.from_yaml(pkgname=pkgname, data=data)
        else: 
            raise ValueError(f'unsupported fetch type "{fetchtype}"')


class GitFetcher(FetchHandler):

    # set this variable to override git clone protocol (e.g., to https)
    proto_override = None
    
    def __init__(self, pkgname, server, repository, tag=None, proto='ssh') -> None:

        super().__init__(pkgname=pkgname)
        self.tag = tag
        self.server = server
        self.repository = repository
        self.proto = proto if self.proto_override is None else self.proto_override
    
    @classmethod
    def from_yaml(cls, pkgname, data):
        return GitFetcher(pkgname=pkgname, 
                          server=data['clone']['server'],
                          repository=data['clone']['repository'],
                          tag=data['clone'].get('tag', None),
                          proto=data['clone'].get('proto', 'ssh'))


    def fetch(self, srcdir) -> bool:

        # create git tools
        git = GitTools(srcdir=srcdir)

        # check existance
        print(f'[{self.pkgname}] cloning source code ...')
        if os.path.exists(srcdir):
            print(f'[{self.pkgname}] source code  already exists, skipping clone')

        elif not git.clone(server=self.server, repository=self.repository, proto=self.proto):
            print(f'[{self.pkgname}] unable to clone source code')
            return False

        elif not git.checkout(tag=self.tag):
            print(f'[{self.pkgname}] unable to checkout tag {self.tag}')
            return False

        return True


class DebFetcher(FetchHandler):

    def __init__(self, pkgname, debname: str) -> None:
        super().__init__(pkgname)
        # note: expand environment variables between {curly braces}
        # example: 'ros-{ROS_DISTRO}-moveit-core` becomes 'ros-melodic-moveit-core'
        self.debname = debname.format(**os.environ)

    
    def fetch(self, srcdir) -> bool:
        print(f'[{self.pkgname}] installing {self.debname} from apt, type password')
        pwd = getpass.getpass()
        return proc_utils.call_process(args=['sudo', '-S', 'apt', 'install', '-y', self.debname], input=pwd)

    
    @classmethod
    def from_yaml(cls, pkgname, data):
        return DebFetcher(pkgname=pkgname, 
                          debname=data['clone']['debname'])
