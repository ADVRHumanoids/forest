import subprocess
import sys 

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
            raise RuntimeError(f'unsupported protocol "{proto}"')
        
        try:
            subprocess.check_output(['git', 'clone', addr, self.srcdir], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print(e.output.decode(), file=sys.stderr)
            return False 

        return True

    def checkout(self, tag):

        try:
            subprocess.check_output(['git', 'checkout', tag], stderr=subprocess.STDOUT, cwd=self.srcdir)
        except subprocess.CalledProcessError as e:
            print(e.output.decode(), file=sys.stderr)
            return False 

        return True
