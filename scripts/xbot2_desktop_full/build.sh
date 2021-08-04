set -e   # return 1 if a command fails

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

# add xbotbuild repo to apt
sh -c 'echo "deb http://xbot.cloud/xbot2/ubuntu/$(lsb_release -sc) /" > /etc/apt/sources.list.d/xbot-latest.list'
wget -q -O - http://xbot.cloud/xbot2/ubuntu/KEY.gpg | apt-key add -
apt update

# source xbot
apt install xbot_env
source /opt/xbot/setup.sh


cd forest
# pip3 install --user -e .
# export PATH=$PATH:/home/user/.local/bin
pip3 install -e .   # system installation (root)
cd ..
mkdir xbot2_forest
cd xbot2_forest
forest --init
source install/setup.bash
forest --add-recipes git@github.com:MarcoRuzzon/forest-recipes.git xbot2-desktop-full
forest xbot2_desktop_full -j8 #-v