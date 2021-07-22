# FROM ros:melodic-desktop-full-bionic
FROM osrf/ros:melodic-desktop-full-bionic
# ENV ROS_DISTRO melodic # not necessary because it is already set by roslib

RUN apt-get update && apt-get install -y \
sudo file libyaml-cpp-dev build-essential cmake cmake-curses-gui libmatio-dev libfmt-dev \
python3-pip wget openssh-client vim
# ros-${ROS_DISTRO}-moveit-core

RUN pip3 install --upgrade pip
RUN pip3 install -U setuptools

WORKDIR /root