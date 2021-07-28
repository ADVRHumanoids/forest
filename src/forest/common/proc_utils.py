import subprocess
import sys 

call_process_verbose = False

def call_process(args, cwd='.', input=None, verbose=False, print_on_error=True):

    if verbose or call_process_verbose:
        print('calling "{}"'.format(' '.join(args)))

    if call_process_verbose or verbose:
        # run will print output to terminal
        proc = subprocess.run(args=args, cwd=cwd, input=input)
        return proc.returncode == 0 

    try:
        # check_output will not print
        subprocess.check_output(args=args, stderr=subprocess.STDOUT, cwd=cwd, input=input)
    except subprocess.CalledProcessError as e:
        # on error, print output
        if print_on_error:
            print(e.output.decode(), file=sys.stderr)
        return False

    return True


def get_output(args, cwd='.', input=None, verbose=False, print_on_error=True):

    if verbose or call_process_verbose:
        print('calling "{}"'.format(' '.join(args)))

    try:
        # check_output will not print
        out = subprocess.check_output(args=args, cwd=cwd, input=input)
        ret = out.decode().strip()
        if verbose or call_process_verbose:
            print('calling "{}" returned "{}"'.format(' '.join(args), ret))
        return ret
    except subprocess.CalledProcessError as e:
        # on error, print output
        if print_on_error:
            print(e.output.decode(), file=sys.stderr)
        return None
