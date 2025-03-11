import os 
import yaml

from tempfile import TemporaryDirectory

from forest.cmake_tools import CmakeTools
from forest.common import eval_handler
from forest.common import print_utils
from forest.common.fetch_handler import CustomFetcher
from forest.common.print_utils import ProgressReporter
from forest.common import proc_utils

class BuildHandler:

    # entries in this cache have already been built
    build_cache = set()

    def __init__(self, pkgname) -> None:
        
        # pkgname
        self.pkgname = pkgname

        # print function to report progress
        self.pprint = ProgressReporter.get_print_fn(pkgname)

        # pre and post build commands
        self.pre_build_cmd = list()
        self.post_build_cmd = list()

        # env hook to install
        self.env_hooks = []

    
    def pre_build(self, builddir, srcdir, installdir):
        eh = eval_handler.EvalHandler.instance()
        process_string = lambda cmd: eh.process_string(cmd, {'builddir':builddir, 
                                                             'srcdir': srcdir, 
                                                             'installdir': installdir})
        
        _pre_build_cmd = map(process_string, self.pre_build_cmd)
        
        # apply locals to all cmds before executing the first one
        pre_build_cmd = list(_pre_build_cmd)

        for cmd in pre_build_cmd:
            proc_utils.call_process(args=[cmd], cwd=builddir, shell=True)

    def post_build(self, builddir, srcdir, installdir):
        eh = eval_handler.EvalHandler.instance()
        process_string = lambda cmd: eh.process_string(cmd, {'builddir':builddir, 
                                                             'srcdir': srcdir, 
                                                             'installdir': installdir})
        
        _post_build_cmd = map(process_string, self.post_build_cmd)
        
        # apply locals to all cmds before executing the first one
        post_build_cmd = list(_post_build_cmd)

        for cmd in post_build_cmd:
            proc_utils.call_process(args=[cmd], cwd=builddir, shell=True)
    
    def install_env_hook(self, installdir):
        if len(self.env_hooks) == 0:
            return 
        
        eh = eval_handler.EvalHandler.instance()
        process_string = lambda cmd: eh.process_string(cmd, {'installdir': installdir})
        env_hooks_processed = map(process_string, self.env_hooks)

        os.makedirs(f'{installdir}/share/forest_env_hook', exist_ok=True)

        with open(f'{installdir}/share/forest_env_hook/{self.pkgname}.bash', 'w') as f:
            for eh in env_hooks_processed:
                f.write(eh + '\n')

        self.pprint('installed environment hook, re-source your setup.bash')

    def build(self, 
              srcdir: str, 
              builddir: str, 
              installdir: str,
              buildtype: str,
              jobs: int,
              reconfigure=False) -> bool:
        """
        Carry out the build procedure for this package.

        Args:
            srcdir (str): directory with source code as cloned by the FetchHandler
            builddir (str): directory where build artifacts must be generated
            installdir (str): directory where the build output will be copied
            buildtype (str): a string describing the build type (e.g., Release)
            jobs (int): number of parallel jobs to use
            reconfigure (bool, optional): flag indicating if configuration step must be forces (cmake specific). Defaults to False.
        """
        
        if self.pkgname in BuildHandler.build_cache:
            return True 

        BuildHandler.build_cache.add(self.pkgname)
        self.pprint('no build action required')
        return True 

    
    @classmethod
    def from_yaml(cls, pkgname, data, recipe):
        buildtype = data['type']
        builder = None
        
        if buildtype == 'cmake':
            builder = CmakeBuilder.from_yaml(pkgname=pkgname, data=data)
        elif buildtype == 'custom':
            builder = CustomBuilder.from_yaml(pkgname=pkgname, data=data)
        else: 
            raise ValueError(f'unsupported build type "{buildtype}"')
        
        # pre and post-build (unconditional)
        pre_build = recipe.get('pre_build', list())
        post_build = recipe.get('post_build', list())

        # conditional
        eh = eval_handler.EvalHandler.instance()

        pre_build_if = recipe.get('pre_build_if', dict())
        pre_build.extend(eh.parse_conditional_dict(pre_build_if))

        post_build_if = recipe.get('post_build_if', dict())
        post_build.extend(eh.parse_conditional_dict(post_build_if))

        builder.pre_build_cmd = pre_build
        builder.post_build_cmd = post_build

        # env hooks
        builder.env_hooks = data.get('env_hooks', list())

        return builder


class CustomBuilder(BuildHandler):

    def __init__(self, pkgname) -> None:
        super().__init__(pkgname)
        self.commands = list()

    def build(self, srcdir: str, builddir: str, installdir: str, buildtype: str, jobs: int, reconfigure=False) -> bool:
        
        # evaluator
        eh = eval_handler.EvalHandler.instance()

        # check if package in cache
        if self.pkgname in BuildHandler.build_cache:
            self.pprint('already built, skipping')
            return True
        
        # create source folder
        if not os.path.exists(srcdir):
            os.mkdir(srcdir)

        self.pprint('building...')
        with TemporaryDirectory(prefix="foresttmp-") as tmpdir:
            ncmd = len(self.commands)
            for i, cmd in enumerate(self.commands):
                cmd_p = eh.process_string(cmd, {'srcdir': srcdir, 'installdir': installdir, 'jobs': jobs})
                self.pprint(f'[{i+1}/{ncmd}] {cmd_p}')
                if not proc_utils.call_process([cmd_p], cwd=tmpdir, shell=True, print_on_error=True):
                    self.pprint(f'{cmd_p} failed')
                    return False 

        # install hooks 
        self.install_env_hook(installdir)

        # save to cache and exit
        BuildHandler.build_cache.add(self.pkgname)
        
        return True 

    @classmethod
    def from_yaml(cls, pkgname, data):
        ret = CustomBuilder(pkgname=pkgname)
        ret.commands = list(data['cmd'])
        return ret

class CmakeBuilder(BuildHandler):

    def __init__(self, pkgname, cmake_args=None, cmakelists='.', target='install') -> None:

        super().__init__(pkgname=pkgname)
        self.cmake_args = cmake_args if cmake_args is not None else list()
        self.cmakelists_folder = cmakelists
        self.target = target
    
    
    @classmethod
    def from_yaml(cls, pkgname, data):

        # check if we must skip this build,
        # and return a dummy builder if so
        eh = eval_handler.EvalHandler.instance()
        skip_condition = data.get('skip_if', 'False')
        if eh.eval_condition(skip_condition):
            return BuildHandler(pkgname=pkgname)

        # first, parse cmake arguments
        args = data.get('args', list())
        args_if = data.get('args_if', dict())

        # parse conditional cmake arguments
        args.extend(eh.parse_conditional_dict(args_if))

        

        return CmakeBuilder(pkgname=pkgname, 
                            cmake_args=args,
                            cmakelists=data.get('cmakelists', '.'),
                            target=data.get('target', 'install'))
    

    def build(self, 
              srcdir: str,
              builddir: str, 
              installdir: str,
              buildtype: str,
              jobs: int,
              reconfigure=False) -> bool:
        
        # check if package in cache
        if self.pkgname in BuildHandler.build_cache:
            self.pprint('already built, skipping')
            return True
        
        srcdir_list = []
        builddir_list = []
        
        if isinstance(self.cmakelists_folder, str):
            srcdir_list = [os.path.join(srcdir, self.cmakelists_folder)]
            builddir_list = [builddir]
        else:
            for item in self.cmakelists_folder:
                sub_name, sub_folder = list(item.items())[0]
                srcdir_list.append(os.path.join(srcdir, sub_folder))
                builddir_list.append(os.path.join(builddir, sub_name))
        

        for srcdir, builddir in zip(srcdir_list, builddir_list):
            
            ret = self._build_single(srcdir=srcdir,
                                     builddir=builddir,
                                     installdir=installdir,
                                     buildtype=buildtype,
                                     jobs=jobs,
                                     reconfigure=reconfigure)
            
            if not ret:
                return False

        return True        


    def _build_single(self, 
              srcdir: str, 
              builddir: str, 
              installdir: str,
              buildtype: str,
              jobs: int,
              reconfigure=False) -> bool:
        
        # create build folder if needed
        if not os.path.exists(builddir):
            os.makedirs(builddir)

        # create cmake tools
        cmake = CmakeTools(srcdir=srcdir, builddir=builddir)

        # configure
        if not cmake.is_configured() or reconfigure:

            # parse additional cmake args through the shell
            # process all args through the shell
            eh = eval_handler.EvalHandler.instance()
            user_cmake_args = []
            for arg in self.cmake_args:
                user_cmake_args.append(eh.process_string(arg, {'srcdir': srcdir, 'installdir': installdir, 'jobs': jobs}))

            # set install prefix and build type (only on first or forced configuration)
            cmake_args = list()
            cmake_args.append(f'-DCMAKE_INSTALL_PREFIX={installdir}')
            cmake_args.append(f'-DCMAKE_BUILD_TYPE={buildtype}')
            cmake_args += user_cmake_args  # note: flags from recipes as last entries to allow override

            self.pprint('running cmake...')
            if not cmake.configure(args=cmake_args):
                self.pprint('configuring failed')
                return False

        # pre-build
        self.pre_build(builddir, srcdir, installdir)

        # build
        self.pprint('building...')
        if not cmake.build(target=self.target, jobs=jobs):
            self.pprint('build failed')
            return False 

        # post-build
        self.post_build(builddir, srcdir, installdir)

        # install hooks 
        self.install_env_hook(installdir)
        
        # save to cache and exit
        BuildHandler.build_cache.add(self.pkgname)
        
        self._cache_install_info(self.pkgname, builddir, installdir)

        return True
    
    def _cache_install_info(self, pkgname, builddir, installdir):        
        manifest_fname = os.path.join(builddir, 'install_manifest.txt')
        if not os.path.isfile(manifest_fname):
            self.pprint(f'missing install_manifest.txt: {manifest_fname}')
            return

        install_cache_dir = os.path.join(installdir, ".install_cache")
        if not os.path.exists(install_cache_dir):
            os.mkdir(install_cache_dir)
            
        install_cache_fname = os.path.join(install_cache_dir, pkgname)
       
        with open(manifest_fname, 'r') as manifest, open(install_cache_fname, "a+") as install_cache: 
            install_cache.write(manifest.read())
