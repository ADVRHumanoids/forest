#!/bin/bash

exit_abnormal() {
  echo "Usage: ./run.sh -p <profile> -d <distro> [-r] [-j <jobs>] [-i]
Example:
    ./run.sh -p forest -d bionic
    ./run.sh -p forest -d bionic -i [-r]    # to enter an interactive session [real time]
    ./run.sh -p forest -d bionic -j 8 [-r]   # to run 8 parallel jobs [real time]"
    exit 1
}

# default jobs from nproc
JOBS=$(nproc)

# parse options
while getopts "p:d:j:ir" options; do
  case "${options}" in
    p) PROFILE=${OPTARG}
       ;;
    d) DISTRO=${OPTARG}
       ;;
    r) REALTIME_FLAG="--privileged -v /dev/rtdm:/dev/rtdm"
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
$REALTIME_FLAG \
-v "$(pwd)"/src:/home/user/forest/src \
-v "$(pwd)"/setup.cfg:/home/user/forest/setup.cfg \
-v "$(pwd)"/setup.py:/home/user/forest/setup.py \
-v "$(pwd)"/MANIFEST.in:/home/user/forest/MANIFEST.in \
-v "$(pwd)"/scripts/$PROFILE:/home/user/scripts \
-v $HOME/.ssh:/home/user/.ssh \
xbot:$DISTRO \
$CMD
