set -e   # return 1 if a command fails

echo user | sudo -S chown -R user.user forest

# Add all ssh keys in .ssh to ssh client agent
eval "$(ssh-agent -s)"
for f in $HOME/.ssh/*
do
  # check extension
  if [ "${f: -4}" == ".pub" ]
  then
    # take action on each file. $f store current file name
    ssh-add "${f:0:-4}"
  fi
done

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
forest --add-recipes git@github.com:MarcoRuzzon/forest-recipes.git xbot2-desktop-full
forest xbot2_desktop_full j$(nproc) -v