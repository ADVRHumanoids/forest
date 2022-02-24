from re import sub
import unittest
import os
import glob 
import subprocess

class TestForestBashWrapper(unittest.TestCase):

    pass


if __name__ == '__main__':
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    bash_test_files = glob.glob(curr_dir + '/test_*.bash')
    bash_test_files.sort()
    print(f'found bash test files in {curr_dir}: {bash_test_files}')
    for f in bash_test_files:
        def do_test(self):
            print(f'\n\n\n>>>>>>> running test {f}')
            subprocess.run(f, check=True)
        setattr(TestForestBashWrapper, os.path.basename(f)[:-5], do_test)

    unittest.main()