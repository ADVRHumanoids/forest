# setup environment
export LD_LIBRARY_PATH=£PREFIX£/lib:$LD_LIBRARY_PATH
export CMAKE_PREFIX_PATH=£PREFIX£:$CMAKE_PREFIX_PATH
export PATH=£PREFIX£/bin:$PATH
export GAZEBO_PLUGIN_PATH=£PREFIX£/lib:$GAZEBO_PLUGIN_PATH
export PYTHONPATH=£PREFIX£/lib/python2.7/dist-packages:£PREFIX£/lib/python3/dist-packages:$PYTHONPATH
export ROS_PACKAGE_PATH=£PREFIX£/share:£PREFIX£/lib:$ROS_PACKAGE_PATH
export PKG_CONFIG_PATH=£PREFIX£/lib/pkgconfig:$PKG_CONFIG_PATH

# source env hooks
for f in £PREFIX£/share/forest_env_hook/*; do source $f; done