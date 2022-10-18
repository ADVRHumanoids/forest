import os
import sys
import glob 
import subprocess

if __name__ == '__main__':

    # set https as default 
    os.putenv('HHCM_FOREST_CLONE_DEFAULT_PROTO', 'https')

    curr_dir = os.path.dirname(os.path.abspath(__file__))
    bash_test_files = glob.glob(curr_dir + '/test_*.bash')
    bash_test_files.sort()
    sep = '\n  - '
    print(f'found bash test files in {curr_dir}: {sep.join(bash_test_files)}')
    
    failed = False
    for f in bash_test_files:
        print(f'\n\n\n>>>>>>> running test {f}')
        try:
            subprocess.run(f, check=True)
        except subprocess.CalledProcessError as e:
            failed = True 
            print(e)

    if failed:
        sys.exit(1)
