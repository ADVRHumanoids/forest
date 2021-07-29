FROM ros:melodic-ros-base-bionic

RUN apt-get update && apt-get install -y \
sudo file libyaml-cpp-dev build-essential cmake cmake-curses-gui openssh-client vim git \
ros-${ROS_DISTRO}-urdf ros-${ROS_DISTRO}-orocos-kdl ros-${ROS_DISTRO}-kdl-parser \
ros-${ROS_DISTRO}-eigen-conversions ros-${ROS_DISTRO}-robot-state-publisher \
ros-${ROS_DISTRO}-interactive-markers ros-${ROS_DISTRO}-tf-conversions ros-${ROS_DISTRO}-tf2-eigen
# libmatio-dev libfmt-dev

RUN apt-get update && apt-get install -y \
libgazebo9-dev \
qttools5-dev libqt5charts5-dev qtdeclarative5-dev \
libglpk-dev

RUN apt-get update && apt-get install -y ros-${ROS_DISTRO}-rviz python3-pip wget
# ros-${ROS_DISTRO}-moveit-core


RUN pip3 install --upgrade pip
RUN pip3 install -U setuptools

WORKDIR /root