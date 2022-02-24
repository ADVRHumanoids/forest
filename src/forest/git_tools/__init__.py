import typing

from forest.common import proc_utils
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
        cmd = ['git', 'clone', '--branch', tag]
        
        if single_branch:
            cmd.append('--single-branch')

        if recursive:
            cmd.append('--recursive')

        if depth is not None:
            cmd.extend(['--depth', depth])

        cmd.extend([addr, self.srcdir])

        # clone, and delete the source folder on failure
        # (either exception or git returns != 0) 
        try:
            clone_ok = proc_utils.call_process(args=cmd)
            if not clone_ok:
                self.rm()
        except BaseException as e:
            # remove src and re-raise exception
            self.rm()
            raise e

        return clone_ok

    def checkout(self, tag):
        return proc_utils.call_process(['git', 'checkout', tag], cwd=self.srcdir)

    def rm(self):
        shutil.rmtree(self.srcdir,  ignore_errors=True)
