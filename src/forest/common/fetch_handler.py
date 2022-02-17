import os 
import shutil
import getpass
from tempfile import TemporaryDirectory

from forest.git_tools import GitTools
from forest.common import proc_utils
from forest.common.print_utils import ProgressReporter
from forest.common.eval_handler import EvalHandler

class FetchHandler:
    
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

        # print function to report progress
        self.pprint = ProgressReporter.get_print_fn(pkgname)

    
    def fetch(self, srcdir):
        """
        Carry out the fetch operation on the package.

        Args:
            srcdir (str): directory where sources are cloned/copied
        """
        self.pprint('no fetch action required')
        return True 

    @classmethod
    def from_yaml(cls, pkgname, data, recipe) -> 'FetchHandler':
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
        elif fetchtype == 'custom':
            return CustomFetcher.from_yaml(pkgname=pkgname, data=data)
        else: 
            raise ValueError(f'unsupported fetch type "{fetchtype}"')


class CustomFetcher(FetchHandler):

    def __init__(self, pkgname) -> None:
        super().__init__(pkgname)
        self.commands = list()

    def fetch(self, srcdir):
        
        # evaluator
        eh = EvalHandler.instance()
        
        if os.path.exists(srcdir):
            self.pprint(f'source code  already exists, skipping clone')
            return True
        
        # create source folder
        os.mkdir(srcdir)

        # run commands
        with TemporaryDirectory(prefix="foresttmp-") as tmpdir:
            for cmd in self.commands:
                cmd_p = eh.process_string(cmd, {'srcdir': srcdir})
                if not proc_utils.call_process([cmd_p], cwd=tmpdir, shell=True, print_on_error=True):
                    self.pprint(f'{cmd_p} failed')
                    shutil.rmtree(srcdir, ignore_errors=True)
                    return False 
        
        return True

    @classmethod
    def from_yaml(cls, pkgname, data):
        ret = CustomFetcher(pkgname=pkgname)
        ret.commands = list(data['cmd'])
        return ret

class GitFetcher(FetchHandler):

    # set this variable to override git clone protocol (e.g., to https)
    proto_override = None

    # this sets the global clone depth
    depth_override = None
    
    def __init__(self, pkgname, server, repository, tag=None, proto='ssh', recursive=False) -> None:

        super().__init__(pkgname=pkgname)
        self.tag = tag
        self.server = server
        self.repository = repository
        self.proto = proto if self.proto_override is None else self.proto_override
        self.recursive = recursive
    
    @classmethod
    def from_yaml(cls, pkgname, data):
        
        eh = EvalHandler.instance()
        
        # process tag
        tag = data['tag']
        tag = eh.process_string(tag)

        # parse tag_if (if present)
        tag_if = data.get('tag_if', dict())
        tag_if_parsed = eh.parse_conditional_dict(tag_if)

        # tag_if has precendence
        if len(tag_if_parsed) == 1:
            tag = tag_if_parsed[0]

        if len(tag_if_parsed) > 1:
            raise RuntimeError(f'[{pkgname}] tag_if conditions must be mutually exclusive')

        return GitFetcher(pkgname=pkgname, 
                          server=data['server'],
                          repository=data['repository'],
                          tag=tag,
                          proto=data.get('proto', 'ssh'),
                          recursive=data.get('recursive', False))


    def fetch(self, srcdir) -> bool:
        
        # custom print shorthand
        pprint = self.pprint

        # create git tools
        git = GitTools(srcdir=srcdir)

        eh = EvalHandler.instance()
        tag_processed = eh.process_string(self.tag)

        # check existance
        if os.path.exists(srcdir):
            pprint(f'source code already exists, skipping clone')
            return True

        pprint(f'cloning source code ({self.proto})...')
        
        if not git.clone(server=self.server, 
                        repository=self.repository, 
                        tag=tag_processed,
                        proto=self.proto, 
                        recursive=self.recursive,
                        depth=GitFetcher.depth_override):
            pprint(f'unable to clone source code (tag {tag_processed})')
            git.rm()
            return False

        return True


class DebFetcher(FetchHandler):

    def __init__(self, pkgname, debname: str) -> None:
        super().__init__(pkgname)
        # note: expand environment variables between {curly braces}
        # example: 'ros-{ROS_DISTRO}-moveit-core` becomes 'ros-melodic-moveit-core'
        self.debname = debname.format(**os.environ)

    
    def fetch(self, srcdir) -> bool:

        # custom print shorthand
        pprint = self.pprint

        pkg_already_installed = proc_utils.call_process(args=['dpkg', '-s', self.debname], print_on_error=False)

        if pkg_already_installed:
            pprint(f'{self.debname} already installed')
            return True
            
        pprint(f'installing {self.debname} from apt')

        return proc_utils.call_process(args=['sudo', 'apt', 'install', '-y', self.debname])

    
    @classmethod
    def from_yaml(cls, pkgname, data):
        return DebFetcher(pkgname=pkgname, 
                          debname=data['debname'])
