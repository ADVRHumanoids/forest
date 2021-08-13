set -e   # return 1 if a command fails

echo user | sudo -Sk chown -R user.user forest

# Add all ssh keys in .ssh to ssh client agent
eval "$(ssh-agent -s)"
for f in $HOME/.ssh/*
do
  # check extension
  if [ "${f: -4}" == ".pub" ]
  # there is a public key
  then
    # add the corresponding private key
    ssh-add "${f:0:-4}"
  fi
done

# add xbotbuild repo to apt
echo user | sudo -S sh -c 'echo "deb http://xbot.cloud/xbot2/ubuntu/$(lsb_release -sc) /" > /etc/apt/sources.list.d/xbot-latest.list'
wget -q -O - http://xbot.cloud/xbot2/ubuntu/KEY.gpg | sudo apt-key add -
echo user | sudo -Sk apt update

# source xbot
echo user | sudo -Sk apt install xbot_env
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
forest all -j$(nproc) -v --debug-pwd user
# expect -f $HOME/scripts/forest_all.expect $(nproc)

forest --add-recipes git@github.com:MarcoRuzzon/forest-recipes.git robots
forest ModularBot_conda_gripper -j$(nproc) -v

set_xbot2_config install/share/ModularBot_conda_gripper/config/ModularBot.yaml
roscore &
roscore_pid="$!"
sleep 5
xbot2-core --hw dummy --verbose &
xbot2_core_pid="$!"

sleep 10
kill $xbot2_core_pid
kill $roscore_pid