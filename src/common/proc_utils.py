import subprocess
import sys 

call_process_verbose = False

def call_process(args, cwd='.', verbose=False, print_on_error=True):

    if call_process_verbose or verbose:
        # Popen will print output to terminal
        proc = subprocess.Popen(args=args, cwd=cwd)
        return proc.wait() == 0

    try:
        # check_output will not print
        subprocess.check_output(args=args, stderr=subprocess.STDOUT, cwd=cwd)
    except subprocess.CalledProcessError as e:
        # on error, print output
        if print_on_error:
            print(e.output.decode(), file=sys.stderr)
        return False

    return True