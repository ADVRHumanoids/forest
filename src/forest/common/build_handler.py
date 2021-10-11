import os 

from forest.cmake_tools import CmakeTools
from forest.common import package, eval_handler
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

    
    def pre_build(self, builddir):
        for cmd in self.pre_build_cmd:
            proc_utils.call_process(args=cmd, cwd=builddir, shell=True)

    def post_build(self, builddir):
        for cmd in self.post_build_cmd:
            proc_utils.call_process(args=cmd, cwd=builddir, shell=True)
    
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
        else: 
            raise ValueError(f'unsupported build type "{buildtype}"')
        
        # pre and post-build (unconditional)
        pre_build = recipe.get('pre_build', list())
        post_build = recipe.get('post_build', list())

        # conditional
        eh = eval_handler.EvalHandler.instance()

        pre_build_if = recipe.get('pre_build_if', dict())
        pre_build.extend(eh.parse_conditional_dict(pre_build_if))
        pre_build = map(eh.process_string, pre_build)

        post_build_if = recipe.get('post_build_if', dict())
        post_build.extend(eh.parse_conditional_dict(post_build_if))
        post_build = map(eh.process_string, post_build)

        # apply
        builder.pre_build_cmd = list(pre_build)
        builder.post_build_cmd = list(post_build)

        return builder


class CmakeBuilder(BuildHandler):

    # set this variable to override git clone protocol (e.g., to https)
    proto_override = None
    

    def __init__(self, pkgname, cmake_args=None, cmakelists='.') -> None:

        super().__init__(pkgname=pkgname)
        self.cmake_args = cmake_args if cmake_args is not None else list()
        self.cmakelists_folder = cmakelists
        self.target = 'install'
    
    
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

        # process all args through the shell
        args = map(eh.process_string, args)

        return CmakeBuilder(pkgname=pkgname, 
                            cmake_args=args,
                            cmakelists=data.get('cmakelists', '.'))


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

        # path to folder containing cmakelists
        cmakelists = os.path.join(srcdir, self.cmakelists_folder)
        
        # create build folder if needed
        if not os.path.exists(builddir):
            os.mkdir(builddir)

        # create cmake tools
        cmake = CmakeTools(srcdir=cmakelists, builddir=builddir)

        # configure
        if not cmake.is_configured() or reconfigure:
            # set install prefix and build type (only on first or forced configuration)
            cmake_args = list()
            cmake_args.append(f'-DCMAKE_INSTALL_PREFIX={installdir}')
            cmake_args.append(f'-DCMAKE_BUILD_TYPE={buildtype}')
            cmake_args += self.cmake_args  # note: flags from recipes as last entries to allow override

            self.pprint('running cmake...')
            if not cmake.configure(args=cmake_args):
                self.pprint('configuring failed')
                return False

        # pre-build
        self.pre_build(builddir)

        # build
        self.pprint('building...')
        if not cmake.build(target=self.target, jobs=jobs):
            self.pprint('build failed')
            return False 

        # post-build
        self.post_build(builddir)
        
        # save to cache and exit
        BuildHandler.build_cache.add(self.pkgname)

        return True

