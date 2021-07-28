from abc import ABC, abstractmethod
import os 

from forest.cmake_tools import CmakeTools
from . import package, eval_handler


class BuildHandler(ABC):

    # entries in this cache have already been built
    build_cache = set()

    def __init__(self, pkgname) -> None:
        self.pkgname = pkgname

    
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
        
        if self.pkgname is BuildHandler.build_cache:
            return True 

        BuildHandler.build_cache.add(self.pkgname)
        print(f'[{self.pkgname}] no build action required')
        return True 

    
    @classmethod
    def from_yaml(cls, pkgname, data):
        buildtype = data['type']
        if buildtype == 'cmake':
            return CmakeBuilder.from_yaml(pkgname=pkgname, data=data)
        else: 
            raise ValueError(f'unsupported build type "{buildtype}"')


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

        # first, parse cmake arguments
        args = data.get('args', list())
        args_if = data.get('args_if', None)

        # parse conditional cmake arguments
        eh = eval_handler.EvalHandler.instance()
        if args_if is not None:
            for k, v in args_if.items():

                add_arg = False

                # check if key is an active mode, 
                # or is an expression returning True
                if k in package.Package.modes:
                    add_arg = True
                elif eh.eval_condition(code=k):
                    add_arg = True
                else:
                    add_arg = False

                if not add_arg:
                    continue

                # extend args with all conditional args
                if isinstance(v, list):
                    args.extend(v)
                else:
                    args.append(v)

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
            print(f'[{self.pkgname}] already built, skipping')
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

            print(f'[{self.pkgname}] running cmake...')
            if not cmake.configure(args=cmake_args):
                print(f'[{self.pkgname}] configuring failed')
                return False

        # build
        print(f'[{self.pkgname}] building...')
        if not cmake.build(target=self.target, jobs=jobs):
            print(f'[{self.pkgname}] build failed')
            return False 
        
        # save to cache and exit
        BuildHandler.build_cache.add(self.pkgname)

        return True

