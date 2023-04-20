import subprocess
import sys
import getpass
import re
import typing
import progressbar

from forest.common import print_utils
from forest.common.parser import update_progress_bar

call_process_verbose = False


def call_process(args: typing.List[str] = None, 
                 cwd='.', 
                 input=None,
                 verbose=False,
                 print_on_error=True, 
                 shell: bool=False,
                 timeout=None,
                 update_regrex_pattern=None,
                 stderr_to_stdout=False
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
        #  # universal_newlines=True equivalent to text=True (backward compatibility)
        #  see https://docs.python.org/3/library/subprocess.html#subprocess.Popen:~:text=Used%20Arguments.-,The%20universal_newlines%20argument%20is%20equivalent%20to%20text%20and%20is%20provided%20for%20backwards%20compatibility.%20By%20default%2C%20file%20objects%20are%20opened%20in%20binary%20mode.,-New%20in%20version
        stderr = subprocess.STDOUT if stderr_to_stdout else subprocess.PIPE
        pr = subprocess.Popen(args=popen_args,
                                stdout=subprocess.PIPE,
                                stderr=stderr, 
                                cwd=cwd, 
                                shell=shell, 
                                executable=executable,
                                universal_newlines=True)
        
        if update_regrex_pattern is not None:
            _progress_bar(pr, update_regrex_pattern)
            
        if pr.wait(timeout=timeout) != 0:
            if print_on_error:
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

def _progress_bar(process, regrex_pattern):
    pbar = progressbar.ProgressBar(maxval=100, \
    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
    pbar.start()
    
    while True:
        line = process.stdout.readline()

        if not line:
            pbar.finish()
            break
            
        update_progress_bar(line, pbar=pbar, regrex_pattern=regrex_pattern)

def _no_progress_bar(process):
    while True:
            line = process.stdout.readline()

            if not line:
                break

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
