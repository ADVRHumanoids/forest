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

# -------------------------------------
source bionic-18.04-2021_07_20_17_45_44/setup.sh
# ----------------------- TO BE REMOVED

cd forest || exit
pip3 install --user -e .
export PATH=$PATH:/home/user/.local/bin
cd ..
mkdir xbot2_forest
cd xbot2_forest || exit
forest --init
source install/setup.bash
forest --add-recipes git@github.com:MarcoRuzzon/forest-recipes.git main
forest --update  # to be removed after fix --add-recipes
forest xbot2_examples -j8
