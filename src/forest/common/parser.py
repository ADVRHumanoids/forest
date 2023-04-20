import re
import progressbar
from time import sleep
import typing


make_regrex_pattern = '\[((?:\s|\d)(?:\s|\d)\d)%\]'
git_regrex_pattern = 'Receiving objects: ((?:\s|\d)(?:\s|\d)\d)% \('


def find_progress(line: str, regrex_pattern) -> float:
    match = re.search(regrex_pattern, line)
    if match is not None:
        progress = float(match.groups()[0])
        return progress
    

def update_progress_bar(line, pbar, regrex_pattern):   
    progress = find_progress(line, regrex_pattern)
    if progress is not None:
        pbar.update(progress)


if __name__ == '__main__':
    make_example = """
Scanning dependencies of target client
Scanning dependencies of target talker
Scanning dependencies of target listener
Scanning dependencies of target malloc_example
Scanning dependencies of target server
Scanning dependencies of target homing_example
Scanning dependencies of target ros_from_rt
[  5%] Building CXX object src/clock/CMakeFiles/clock_example.dir/clock.cpp.o
[ 20%] Building CXX object src/talker_listener/CMakeFiles/talker.dir/talker.cpp.o
[ 20%] Building CXX object src/malloc_example/CMakeFiles/malloc_example.dir/malloc_example.cpp.o
[ 20%] Building CXX object src/talker_listener/CMakeFiles/listener.dir/listener.cpp.o
[ 25%] Building CXX object src/client_server/CMakeFiles/client.dir/client.cpp.o
[ 30%] Building CXX object src/client_server/CMakeFiles/server.dir/server.cpp.o
[ 35%] Building CXX object src/homing_example/CMakeFiles/homing_example.dir/homing_example.cpp.o
[ 40%] Building CXX object src/ros_from_rt/CMakeFiles/ros_from_rt.dir/ros_from_rt.cpp.o
[ 45%] Linking CXX shared library libxbotctrl_homing_example.so
[ 45%] Built target homing_example
Scanning dependencies of target joint_impedance
[ 50%] Building CXX object src/joint_impedance/CMakeFiles/joint_impedance.dir/joint_impedance.cpp.o
[ 55%] Linking CXX shared library libxbotctrl_malloc_example.so
[ 55%] Built target malloc_example
Scanning dependencies of target cartesio_rt
[ 60%] Building CXX object src/cartesio/CMakeFiles/cartesio_rt.dir/cartesio_rt.cpp.o
[ 65%] Linking CXX shared library libxbotctrl_clock_example.so
[ 65%] Built target clock_example
[ 70%] Linking CXX shared library libxbotctrl_talker.so
[ 70%] Built target talker
[ 75%] Linking CXX shared library libxbotctrl_listener.so
[ 75%] Built target listener
[ 80%] Linking CXX shared library libxbotctrl_server.so
[ 80%] Built target server
[ 85%] Linking CXX shared library libxbotctrl_client.so
[ 85%] Built target client
[ 90%] Linking CXX shared library libxbotctrl_joint_impedance.so
[ 90%] Built target joint_impedance
[ 95%] Linking CXX shared library libxbotctrl_ros_from_rt.so
[ 95%] Built target ros_from_rt
[100%] Linking CXX shared library libxbotctrl_cartesio_rt.so
[100%] Built target cartesio_rt
"""
    pbar = progressbar.ProgressBar(maxval=100, \
    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
    pbar.start()
    for line in make_example.splitlines():
        sleep(0.1)
        update_progress_bar(line, pbar=pbar, regrex_pattern=make_regrex_pattern)
    pbar.finish()


    git_example = """
Cloning into '/home/mruzzon/alberobotics/sps_forest/src/ReflexxesTypeII'...
remote: Enumerating objects: 279, done.
remote: Counting objects: 100% (6/6), done.
remote: Compressing objects: 100% (4/4), done.
remote: Total 279 (delta 2), reused 6 (delta 2), pack-reused 273
Receiving objects:  50% (279/279), 3.35 MiB | 4.62 MiB/s, done.
Resolving deltas: 100% (109/109), done.
returned 0
calling "git checkout master"
Already on 'master'
Your branch is up to date with 'origin/master'.
returned 0
"""

    pbar = progressbar.ProgressBar(maxval=100, \
    widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
    pbar.start()
    for line in git_example.splitlines():
        sleep(0.1)
        update_progress_bar(line, pbar=pbar, regrex_pattern=git_regrex_pattern)
    pbar.finish()