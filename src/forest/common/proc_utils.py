import subprocess
import sys
import typing
import progressbar
import os

from forest.common import print_utils
from forest.common.parser import update_progress_bar
from forest.common.forest_dirs import rootdir

call_process_verbose = False


def call_process(args: typing.List[str] = None, 
                 cwd='.', 
                 input=None,
                 verbose=False,
                 print_on_error=True, 
                 shell: bool=False,
                 timeout=None,
                 update_regrex_pattern=None
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
        pr = subprocess.Popen(args=popen_args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, 
                                cwd=cwd, 
                                shell=shell, 
                                executable=executable,
                                universal_newlines=True)
        
        lines = []
        if update_regrex_pattern is not None:
            lines = _progress_bar(pr, update_regrex_pattern)
            
        if pr.wait(timeout=timeout) != 0:
            if lines:
                print_utils.log_file.writelines(lines)
            else:
                print_utils.log_file.write(pr.stdout.read())
            
            if print_on_error and not verbose:
                print_utils.log_file.seek(0)  # go to the beginning of the file
                print(print_utils.log_file.read(), file=sys.stderr)

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
    lines = []

    while True:
        line = process.stdout.readline()
        lines.append(line)

        if not line:
            pbar.finish()
            return lines
            
        update_progress_bar(line, pbar=pbar, regrex_pattern=regrex_pattern)


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
