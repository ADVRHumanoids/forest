#!/bin/bash

exit_abnormal() {
  echo "Usage: ./docker-build -d distro
Example:
    ./docker-build -d bionic
    "

    exit 1
}

# parse options
while getopts ":d:" options; do
  case "${options}" in
    d) DISTRO=${OPTARG}
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

if [ "$DISTRO" = "" ]; then
  echo "-d <distro> option missing"
  exit_abnormal
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd $DIR

source $DISTRO/update_docker.sh
docker build --tag xbot:$DISTRO . -f $DISTRO/Dockerfile