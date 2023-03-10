import subprocess
import sys
import getpass
import re
import typing

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
                        executable=executable)

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


def call_process_stdout_readline_cb(args: typing.List[str] = None, 
                                    callable: typing.Callable[[str], None]=None, 
                                    cwd='.', 
                                    shell: bool=False,
                                    timeout=None,
                                    verbose=False) -> bool:    
    # convert args to string
    # args = list(map(str, args))    
    if args is None:
        args = []
    
    if verbose or call_process_verbose:
        if shell:
            print(f'calling shell with command "{args}"')
        else:
            print('calling "{}"'.format(' '.join(args)))
    
    if shell:
        executable = '/bin/bash'
        popen_args = ' ' + ' '.join(args) 
    
    else:
        executable = None
        popen_args = args

    if call_process_verbose or verbose:
        # run will print output to terminal
        proc = subprocess.run(args=args, 
                        cwd=cwd, 
                        input=input, 
                        shell=shell, 
                        executable=executable)

        print(f'returned {proc.returncode}')

        return proc.returncode == 0 

    proc = subprocess.Popen(args=popen_args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, 
                            cwd=cwd, 
                            shell=shell, 
                            executable=executable,
                            text=True)
    
    while True:
        line = proc.stdout.readline()

        if not line:
            break
        
        if callable is not None:
            callable(line)
        
    return proc.wait(timeout=timeout) == 0
