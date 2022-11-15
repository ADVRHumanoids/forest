# setup environment
PYTHON_3_VERSION=`python3 -c 'import sys; version=sys.version_info[:3]; print("{0}.{1}".format(*version))'`

# for --prefix --editable installation to fork in forest workspace (.pth files)
site_packages_dir=£PREFIX£/lib/python$PYTHON_3_VERSION/site-packages

echo "import site
site.addsitedir('$site_packages_dir')" > $site_packages_dir/sitecustomize.py

export LD_LIBRARY_PATH=£PREFIX£/lib:$LD_LIBRARY_PATH
export CMAKE_PREFIX_PATH=£PREFIX£:$CMAKE_PREFIX_PATH
export PATH=£PREFIX£/bin:$PATH
export GAZEBO_PLUGIN_PATH=£PREFIX£/lib:$GAZEBO_PLUGIN_PATH
export PYTHONPATH=£PREFIX£/lib/python2.7/dist-packages:£PREFIX£/lib/python3/dist-packages:$site_packages_dir:$PYTHONPATH
export ROS_PACKAGE_PATH=£ROOTDIR£/ros_src:£PREFIX£/share:£PREFIX£/lib:$ROS_PACKAGE_PATH
export PKG_CONFIG_PATH=£PREFIX£/lib/pkgconfig:$PKG_CONFIG_PATH
export HHCM_FOREST_PATH=£ROOTDIR£:$HHCM_FOREST_PATH

# source env hooks
if [ -d £PREFIX£/share/forest_env_hook ]; then
    for f in £PREFIX£/share/forest_env_hook/*; do source $f; done
fi
