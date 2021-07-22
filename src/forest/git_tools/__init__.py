from forest.common import proc_utils

class GitTools:

    def __init__(self, srcdir) -> None:
        self.srcdir = srcdir

    def clone(self, server : str, repository : str, proto='ssh'):
        if proto == 'ssh':
            addr = f'git@{server}:{repository}'
        elif proto == 'https':
            addr = f'https://{server}/{repository}'
        else:
            # TODO more specific exception
            raise ValueError(f'unsupported protocol "{proto}"')
        
        return proc_utils.call_process(args=['git', 'clone', addr, self.srcdir])

    def checkout(self, tag):

        return proc_utils.call_process(['git', 'checkout', tag], cwd=self.srcdir)
