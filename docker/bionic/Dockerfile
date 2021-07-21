# FROM ros:melodic-desktop-full-bionic
FROM osrf/ros:melodic-desktop-full-bionic
ENV rosdistro melodic

RUN apt-get update && apt-get install -y \
sudo file libyaml-cpp-dev build-essential cmake cmake-curses-gui libmatio-dev libfmt-dev \
python3-pip wget ros-${rosdistro}-moveit-core openssh-client vim

RUN pip3 install --upgrade pip
RUN pip3 install -U setuptools

# add regular user
RUN useradd -ms /bin/bash user
RUN adduser user sudo
RUN echo 'user:user' | chpasswd

WORKDIR /home/user

# -------------------------------------
RUN wget http://54.73.207.169/nightly/xbot2-full-devel/bionic-nightly.tar.gz \
&& tar zxvpf bionic-nightly.tar.gz && rm bionic-nightly.tar.gz

RUN cd bionic-18.04-2021_07_20_17_45_44 \
&& ./install.sh

RUN dpkg -r cartesian_interface \
&& dpkg -r xbot2
# ----------------------- TO BE REMOVED

USER user
