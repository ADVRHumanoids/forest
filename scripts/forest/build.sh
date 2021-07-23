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

# Install Xbot2 binaries ----------------
wget http://54.73.207.169/nightly/xbot2-full-devel/bionic-nightly.tar.gz
tar zxvpf bionic-nightly.tar.gz
rm bionic-nightly.tar.gz

cd bionic* || return 1
./install.sh

dpkg -r cartesian_interface
dpkg -r xbot2

source setup.sh
cd ..
# ----------------------- TO BE REMOVED

cd forest || return 1
# pip3 install --user -e .
# export PATH=$PATH:/home/user/.local/bin
pip3 install -e .   # system installation (root)
cd ..
mkdir xbot2_forest
cd xbot2_forest || return 1
forest --init
source install/setup.bash
forest --add-recipes git@github.com:MarcoRuzzon/forest-recipes.git main
forest xbot2_examples -j8
