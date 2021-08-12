FROM ros:melodic-ros-base-bionic

RUN apt-get update && apt-get install -y \
sudo file build-essential cmake cmake-curses-gui openssh-client vim git python3-pip wget

RUN pip3 install --upgrade pip
RUN pip3 install -U setuptools

RUN useradd -ms /bin/bash user
RUN adduser user sudo
RUN echo 'user:user' | chpasswd

USER user

WORKDIR /home/user