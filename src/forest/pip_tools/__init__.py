from forest.common import proc_utils

PIP_COMMAND = 'python3 -m pip install'

class PipTools:

    def __init__(self, srcdir, installdir):
        self.srcdir = srcdir
        self.installdir = installdir

    def build(self, editable=False):
        args = ['--prefix', self.installdir]
        
        if editable:
            args.append('-e')
        
        args.append(self.srcdir)

        return self._call_pip(args)

    @staticmethod
    def _call_pip(args, print_on_error=True):

        args_str = list(map(str, args))
        return proc_utils.call_process(args=PIP_COMMAND.split(' ') + args_str, print_on_error=print_on_error)
