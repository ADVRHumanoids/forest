import typing

from forest.common import proc_utils
import shutil

class GitTools:

    def __init__(self, srcdir) -> None:
        self.srcdir = srcdir

    def clone(self,
              server: str,
              repository: str,
              proto='ssh',
              recursive=False,
              branch: typing.Optional[str] = None,
              single_branch=False) -> bool:
        if proto == 'ssh':
            addr = f'git@{server}:{repository}'
        elif proto == 'https':
            addr = f'https://{server}/{repository}'
        else:
            # TODO more specific exception
            raise ValueError(f'unsupported protocol "{proto}"')
        
        cmd = ['git', 'clone', addr, self.srcdir]
        if single_branch:
            cmd.insert(2, '--single-branch')

        if branch is not None:
            cmd.insert(2, '-b')
            cmd.insert(3, branch)

        if recursive:
            cmd.insert(2, '--recursive')

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

