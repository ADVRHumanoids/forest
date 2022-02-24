import subprocess
import sys
import getpass
import re

from forest.common import print_utils

call_process_verbose = False

def call_process(args, cwd='.', input=None, verbose=False, print_on_error=True, shell=False) -> bool:

    # convert args to string
    args = list(map(str, args))

    if verbose or call_process_verbose:
        if shell:
            print(f'calling shell with command "{args}"')
        else:
            print('calling "{}"'.format(' '.join(args)))

    executable = '/bin/bash' if shell else None

    if call_process_verbose or verbose:
        # run will print output to terminal
        proc = subprocess.run(args=args, 
                        cwd=cwd, 
                        input=input, 
                        shell=shell, 
                        executable=executable)

        print(f'returned {proc.returncode}')

        return proc.returncode == 0 

    try:
        # run with output/error redirection and exit status check
        pr = subprocess.run(args=args, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT, 
                        cwd=cwd, 
                        input=input, 
                        shell=shell, 
                        executable=executable,
                        check=True)

        print_utils.log_file.write(pr.stdout.decode())

    except subprocess.CalledProcessError as e:
        # on error, print output (includes stderr)
        print_utils.log_file.write(e.output.decode())

        if print_on_error and not verbose:
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

