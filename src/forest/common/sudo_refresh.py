import multiprocessing
import psutil
import os
import subprocess
import time

from forest.common import proc_utils

class SudoRefresher:

    """
    SudoRefresher spawns a process that keeps sudo's session alive forever.
    """

    def __init__(self, pwd=None) -> None:

        # first call to sudo is done inside parent process (sync)
        SudoRefresher._do_sudo(pwd)
        print('')  # needed to add newline after sudo's prompt

        # then, start background process
        parent_pid = os.getpid()
        multiprocessing.set_start_method('spawn')
        self.proc = multiprocessing.Process(
                target=SudoRefresher._do_sudo_refresh, 
                args=(parent_pid, pwd)
                )
        self.proc.start()

    def _do_sudo(pwd):

        # password not provided, sudo's prompt will be used
        if pwd is None:
            args = ['sudo', '-v']  # sudo -v extends credentials 
            input = None
        else:
            args = ['sudo', '-S', '-v', '--prompt', '[sudo] got password']
            input = (pwd + '\n').encode()

        try:
            subprocess.check_output(args=args, input=input)
        except subprocess.CalledProcessError as e:
            print(f'could not call "sudo -v": {e.stderr}')


    def _do_sudo_refresh(parent_pid, pwd):

        if proc_utils.call_process_verbose:
            print(f'[sudo refreshing loop] started with pid {os.getpid()}')

        while psutil.pid_exists(parent_pid):
            SudoRefresher._do_sudo(pwd)
            time.sleep(60)
            
    
    def __del__(self):
        self.proc.terminate()  # we don't need clean termination
        self.proc.join(timeout=5)
        if self.proc.exitcode is None:
            print('warning: sudo refresher has not terminated yet')
        else:
            pass  # normal termination
