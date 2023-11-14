import typing

from forest.common import proc_utils
from forest.common.parser import git_regrex_pattern
import shutil


class GitTools:

    def __init__(self, srcdir) -> None:
        self.srcdir = srcdir

    def clone(self, 
            server: str, 
            repository: str, 
            tag: str,
            proto='ssh', 
            recursive=False,
            depth=None,
            single_branch=False):

        if proto == 'ssh':
            addr = f'git@{server}:{repository}'
        elif proto == 'https':
            addr = f'https://{server}/{repository}'
        else:
            # TODO more specific exception
            raise ValueError(f'unsupported protocol "{proto}"')
        
        # create command
        # --progress flag forces progress status even if the standard 
        # error stream is not directed to a terminal.

        cmd = ['git', 'clone', '--progress']
        
        # we're asked to clone a single branch
        # note: it cannot be a commit sha1
        if single_branch:
            cmd.extend(['--branch', tag])
            cmd.append('--single-branch')

        if recursive:
            cmd.append('--recursive')
            if tag is not None:
                cmd.extend(['--branch', tag])

        # note: depth should imply single branch
        if depth is not None:
            cmd.extend(['--branch', tag])
            cmd.append('--single-branch')
            cmd.extend(['--depth', depth])

        cmd.extend([addr, self.srcdir])

        # clone, and delete the source folder on failure
        # (either exception or git returns != 0) 
        try:
            # Progress status is reported on the standard error stream
            clone_ok = proc_utils.call_process(args=cmd, 
                                               update_regrex_pattern=git_regrex_pattern)
            
            # checkout to requested branch/tag/commit
            if tag is not None:
                clone_ok = clone_ok and self.checkout(tag=tag)
            
            if not clone_ok:
                self.rm()
        except BaseException as e:
            # remove src and re-raise exception
            self.rm()
            raise e

        return clone_ok

    def checkout(self, tag):
        # note: does not discover or initialize any new submodules that may be present in the branch being checked out.
        return proc_utils.call_process(['git', 'checkout', '--recurse-submodules', tag], cwd=self.srcdir)
    
    def discover_and_init_submodules(self):
        return proc_utils.call_process(['git', 'submodule', 'sync', '--recursive', '&&',
                                        'git', 'submodule', 'update', '--init', '--recursive'], cwd=self.srcdir)

    def rm(self):
        shutil.rmtree(self.srcdir,  ignore_errors=True)
