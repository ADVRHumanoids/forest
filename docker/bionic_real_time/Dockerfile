FROM ros:melodic-ros-base-bionic

RUN apt-get update && apt-get install -y \
sudo file build-essential cmake cmake-curses-gui openssh-client vim git python3-pip python-pip wget expect

RUN apt-get update && apt-get install -y \
    libelf-dev aptitude apt-file libssl-dev git-core binutils bison flex bc ca-certificates libssl-dev \
    tzdata locales psmisc rsync lshw ethtool wget curl unzip ntp less vim bash-completion openssh-server \
    avahi-daemon nfs-common autotools-dev autoconf libfuse-dev libncurses5-dev libcap2-bin uuid-dev \
    pkg-config usbutils wireless-tools libboost-all-dev libzmq5 libyaml-cpp-dev protobuf-compiler \
    libprotobuf-dev libeigen3-dev libjsoncpp-dev libspnav-dev \
    libtool udev gdb

RUN apt-file update

RUN useradd -ms /bin/bash user
RUN adduser user sudo
RUN echo 'user:user' | chpasswd

RUN chown -R user.user /usr/local/

RUN groupadd -f xenomai
RUN usermod -a -G xenomai user

USER user

RUN python3 -m pip install --user --upgrade pip
RUN python3 -m pip install --user --upgrade setuptools

RUN python2 -m pip install --user --upgrade "pip < 21.0"
RUN python2 -m pip install --user --upgrade setuptools

WORKDIR /home/user
