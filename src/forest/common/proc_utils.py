import subprocess
import sys
import getpass
import re
import typing
import progressbar

from forest.common import print_utils
from forest.common.parser import update_progess_bar

call_process_verbose = False


def call_process(args: typing.List[str] = None, 
                 cwd='.', 
                 input=None,
                 verbose=False,
                 print_on_error=True, 
                 shell: bool=False,
                 timeout=None,
                 ) -> bool:    
    
    # convert args to string
    args = list(map(str, args))    
    
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


    try:
        pr = subprocess.Popen(args=popen_args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, 
                                cwd=cwd, 
                                shell=shell, 
                                executable=executable,
                                text=True)
        
        pbar = progressbar.ProgressBar(maxval=100, \
        widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
        pbar.start()
        while True:
            line = pr.stdout.readline()

            if not line:
                pbar.finish()
                break
                

            update_progess_bar(line, pbar=pbar)
            
        if pr.wait(timeout=timeout) != 0:
            print(pr.stderr.read(), file=sys.stderr)
            return False
        
        return True

    
    #todo: fix subprocess.CalledProcessError not working with subprocess.Popen
    except subprocess.CalledProcessError as e:
        # on error, print output (includes stderr)
        print_utils.log_file.write(e.output.decode())

        if print_on_error and not verbose:
            print(e.output.decode(), file=sys.stderr)
            
        return False


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
