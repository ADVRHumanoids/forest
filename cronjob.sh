#!/bin/bash

exit_abnormal() {
  echo "Usage: ./cronjob.sh -p <profile> -d <distro> [-r] [-j <jobs>] [-l <logfolder_path>] [-f <forestfolder_path>]
Example:
    ./run.sh -p forest -d bionic
    ./run.sh -p forest -d bionic -j 8 [-r] [-l $HOME] [-f $HOME/forest]"
    exit 1
}

# default inputs
PROFILE=forest
DISTRO=bionic_bare_bones
REALTIME_FLAG=
JOBS=$(nproc)
LOGFOLDER=$HOME/forest-logs
FOREST_FOLDER=$HOME

# parse options
while getopts "p:d:j:lfr" options; do
  case "${options}" in
    p) PROFILE=${OPTARG}
       ;;
    d) DISTRO=${OPTARG}
       ;;
    r) REALTIME_FLAG="-r"
       ;;
    j) JOBS=${OPTARG}
       ;;
    l) LOGFOLDER=${OPTARG}
       ;;
    f) FOREST_FOLDER=${OPTARG}
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

# other parameters
DATE=$(date +"%H_%M_%d_%m_%y")
LOGFNAME=$LOGFOLDER/failed_${PROFILE}_${DISTRO}_${DATE}.log

# check log folder exists
if [ ! -d $LOGFOLDER ]; then
  mkdir -p $LOGFOLDER;
fi

temp_logfile=$(mktemp)

# store stdout and stderr in a tm file
$FOREST_FOLDER/forest/docker-run.sh -p $PROFILE -d $DISTRO -j$JOBS $REALTIME_FLAG > temp_logfile 2>&1
if [ $? -ne 0 ]; then
  # in case of errors save the log
  cp temp_logfile $LOGFNAME
fi

rm ${temp_logfile}