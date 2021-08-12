set -e   # return 1 if a command fails

echo user | sudo -S chown -R user.user forest

# Add all ssh keys in .ssh to ssh client agent
eval "$(ssh-agent -s)"
for f in $HOME/.ssh/*
do
  # check extension
  if [ "${f: -4}" != ".pub" ] && [ "$f" != "$HOME/.ssh/known_hosts" ]
  then
    # take action on each file. $f store current file name
    ssh-add "$f"
  fi
done

#xenomai
git clone -b v3.1.x_cmake git@gitlab.advr.iit.it:amargan/xenomai.git
pushd xenomai
./scripts/bootstrap
./configure --enable-pshared --enable-tls --enable-dlopen-libs --enable-async-cancel --enable-smp
make -j$(nproc)
echo user | sudo -S make install
popd

echo /usr/xenomai/lib/ > xenomai.conf
echo user | sudo -S cp -f xenomai.conf /etc/ld.so.conf.d/
echo user | sudo -S ldconfig

echo user | sudo -S cp -f /usr/xenomai/etc/udev/rules.d/rtdm.rules /etc/udev/rules.d/

echo user | sudo -S udevadm control --reload-rules
echo user | sudo -S udevadm trigger

echo "export PATH=$PATH:/usr/xenomai/bin" >> .bashrc
source .bashrc


# add xbotbuild repo to apt
echo user | sudo -S sh -c 'echo "deb http://xbot.cloud/xbot2/ubuntu/$(lsb_release -sc) /" > /etc/apt/sources.list.d/xbot-latest.list'
wget -q -O - http://xbot.cloud/xbot2/ubuntu/KEY.gpg | sudo apt-key add -
echo user | sudo -S apt update

# source xbot
echo user | sudo -S apt install xbot_env
source /opt/xbot/setup.sh

pushd forest
pip3 install --user -e .
export PATH=$PATH:/home/user/.local/bin
# pip3 install -e .   # system installation (root)
popd
mkdir xbot2_forest
cd xbot2_forest
forest --init
source install/setup.bash
forest --add-recipes git@github.com:MarcoRuzzon/forest-recipes.git xeno
forest all -j$(nproc) --mode xeno -v

forest --add-recipes git@github.com:MarcoRuzzon/forest-recipes.git robots
forest ModularBot_conda_gripper -j$(nproc) --mode xeno -v

set_xbot2_config install/share/ModularBot_conda_gripper/config/ModularBot.yaml
roscore&
roscore_pid="$!"
sleep 5
xbot2-core --hw dummy --verbose &
xbot2_core_pid="$!"

sleep 10
kill $xbot2_core_pid
kill $roscore_pid
