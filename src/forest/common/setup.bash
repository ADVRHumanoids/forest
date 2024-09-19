# setup environment
export LD_LIBRARY_PATH=£PREFIX£/lib:$LD_LIBRARY_PATH
export CMAKE_PREFIX_PATH=£PREFIX£:$CMAKE_PREFIX_PATH
export PATH=£PREFIX£/bin:$PATH
export GAZEBO_PLUGIN_PATH=£PREFIX£/lib:$GAZEBO_PLUGIN_PATH
export PYTHONPATH=£PREFIX£/lib/python2.7/dist-packages:£PREFIX£/£REL_SITE_PKG_PATH£:£PREFIX£/lib/python3/dist-packages:$PYTHONPATH
export ROS_PACKAGE_PATH=£ROOTDIR£/ros_src:£PREFIX£/share:£PREFIX£/lib:$ROS_PACKAGE_PATH
export AMENT_PREFIX_PATH=£ROOTDIR£/install:$AMENT_PREFIX_PATH
export PKG_CONFIG_PATH=£PREFIX£/lib/pkgconfig:$PKG_CONFIG_PATH
export HHCM_FOREST_PATH=£ROOTDIR£:$HHCM_FOREST_PATH

# source env hooks
if [ -d £PREFIX£/share/forest_env_hook ]; then
    for f in £PREFIX£/share/forest_env_hook/*; do source $f; done
fi

# activate venv
if [ -d £ROOTDIR£/venv ]; then
    source £ROOTDIR£/venv/bin/activate
fi
