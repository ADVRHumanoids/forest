#!/bin/bash

exit_abnormal() {
  echo "Usage: ./run.sh -p <profile> -d <distro> [-j <jobs>] [-i]
Example:
    ./run.sh -p forest -d bionic
    ./run.sh -p forest -d bionic -i     # to enter an interactive session
    ./run.sh -p forest -d bionic -j 8   # to run 8 parallel jobs"

    exit 1
}

# default jobs from nproc
JOBS=$(nproc)

# parse options
while getopts "p:d:j:i" options; do
  case "${options}" in
    p) PROFILE=${OPTARG}
       ;;
    d) DISTRO=${OPTARG}
       ;;
    j) JOBS=${OPTARG}
       ;;
    i) DOCKERFLAG="-it"
       ;;
    :)
      echo "Error: -${OPTARG} requires an argument."
      exit_abnormal
      ;;
    *)
      exit_abnormal
      ;;
  esac
done

if [ "$PROFILE" = "" ]; then
  echo "-p <profile> option missing"
  exit_abnormal
fi

if [ "$DISTRO" = "" ]; then
  echo "-d <distro> option missing"
  exit_abnormal
fi


# exit on error
set -e

# get path to script and change working directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR


echo "Running container for profile = '$PROFILE', distro = '$DISTRO'"

# build docker image
./docker/docker-build.sh -d $DISTRO

# command to run inside docker
if [ "$DOCKERFLAG" = "-it" ]; then
  CMD="bash"  # if interactive mode, spawn a bash session
else
  CMD="./scripts/build.sh -j$JOBS -s"  # else, run the build script
fi

# run the container
docker run $DOCKERFLAG --rm \
--env="DISPLAY" \
--name forest_"$DISTRO" \
-v "$(pwd)"/src:/home/user/forest/src \
-v "$(pwd)"/setup.cfg:/home/user/forest/setup.cfg \
-v "$(pwd)"/setup.py:/home/user/forest/setup.py \
-v "$(pwd)"/MANIFEST.in:/home/user/forest/MANIFEST.in \
-v "$(pwd)"/scripts/$PROFILE:/home/user/scripts \
-v $HOME/.ssh:/home/user/.ssh \
xbot:$DISTRO \
$CMD