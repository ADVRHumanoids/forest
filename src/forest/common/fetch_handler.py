from abc import ABC, abstractmethod
import os 
import getpass
import subprocess 

from forest.git_tools import GitTools
from . import proc_utils

class FetchHandler(ABC):
    
    """
    Abstract interface to a fetch handler, i.e., a class that incorporates
    the logic behind the fetching of a package's source code.
    As an exception, we also consider this base class to describe the process
    of fetching binary distributions such as debian packages (even though in
    this case sources are not involved).
    
    Concrete instances of this class are created via the from_yaml() factory method.
    """

    def __init__(self, pkgname) -> None:
        """
        Construct the FetchHandler

        Args:
            pkgname (str): name of the package
        """
        self.pkgname = pkgname

    
    def fetch(self, srcdir):
        """
        Carry out the fetch operation on the package.

        Args:
            srcdir (str): directory where sources are cloned/copied
        """
        print(f'[{self.pkgname}] no fetch action required')
        return True 

    @classmethod
    def from_yaml(cls, pkgname, data) -> 'FetchHandler':
        """ 
        Factory method to instantiate concrete fetchers given their
        yaml description.

        Args:
            pkgname (str): name of the package
            data (dict): the 'clone' entry of the yaml recipe, parsed 
            into a python dictionary

        Raises:
            ValueError: the specified fetcher type is not supported

        Returns:
            FetchHandler: the requested object
        """

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
                          server=data['server'],
                          repository=data['repository'],
                          tag=data.get('tag', None),
                          proto=data.get('proto', 'ssh'))


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

    # user password
    pwd = None 

    def __init__(self, pkgname, debname: str) -> None:
        super().__init__(pkgname)
        # note: expand environment variables between {curly braces}
        # example: 'ros-{ROS_DISTRO}-moveit-core` becomes 'ros-melodic-moveit-core'
        self.debname = debname.format(**os.environ)

    
    def fetch(self, srcdir) -> bool:

        pkg_already_installed = proc_utils.call_process(args=['dpkg', '-s', self.debname], print_on_error=False)

        if pkg_already_installed:
            print(f'[{self.pkgname}] {self.debname} already installed')
            return True
            
        print(f'[{self.pkgname}] installing {self.debname} from apt')
        
        if DebFetcher.pwd is None:
            pwd = getpass.getpass()
            DebFetcher.pwd = (pwd + '\n').encode()

        return proc_utils.call_process(args=['sudo', '-Sk', 'apt', 'install', '-y', self.debname], 
                                       input=DebFetcher.pwd)

    
    @classmethod
    def from_yaml(cls, pkgname, data):
        return DebFetcher(pkgname=pkgname, 
                          debname=data['debname'])
