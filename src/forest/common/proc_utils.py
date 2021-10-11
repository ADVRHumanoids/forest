import subprocess
import sys 
from forest.common import print_utils

call_process_verbose = False

def call_process(args, cwd='.', input=None, verbose=False, print_on_error=True, shell=False):

    if verbose or call_process_verbose:
        if shell:
            print(f'calling shell with command "{args}"')
        else:
            print('calling "{}"'.format(' '.join(args)))

    if call_process_verbose or verbose:
        # run will print output to terminal
        proc = subprocess.run(args=args, cwd=cwd, input=input, shell=shell)
        return proc.returncode == 0 

    try:
        # check_output will not print
        # note that we redirect stderr to stdout!
        subprocess.check_output(args=args, stdout=print_utils.log_file, stderr=subprocess.STDOUT, cwd=cwd, input=input, shell=shell)
    except subprocess.CalledProcessError as e:
        # on error, print output (includes stderr)
        if print_on_error:
            print(e.output.decode(), file=sys.stderr)
        return False

    return True


def get_output(args, cwd='.', input=None, verbose=False, print_on_error=True, shell=False):

    if verbose or call_process_verbose:
        if shell:
            print(f'calling shell with command "{args}"')
        else:
            print('calling "{}"'.format(' '.join(args)))

    try:
        # check_output will not print
        out = subprocess.check_output(args=args, cwd=cwd, input=input, shell=shell)
        ret = out.decode().strip()
        if verbose or call_process_verbose:
            print('calling "{}" returned "{}"'.format(' '.join(args), ret))
        return ret
    except subprocess.CalledProcessError as e:
        # on error, print output and errors
        if print_on_error:
            print('stdout: ' + e.output.decode(), file=sys.stderr)
            print('stderr: ' + e.stderr.decode(), file=sys.stderr)
        return None
