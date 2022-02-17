# the temp directory used, within $DIR
# omit the -p parameter to create a temporal directory in the default location
WORK_DIR=`mktemp -d -p "$DIR"`

# check if tmp dir was created
if [[ ! "$WORK_DIR" || ! -d "$WORK_DIR" ]]; then
  echo "Could not create temp dir"
  exit 1
fi

# deletes the temp directory
function workdir_cleanup {      
  rm -rf "$WORK_DIR"
  echo "Deleted temp working directory $WORK_DIR"
  if [[ "$SUCCESS" == "1" ]]; then 
    echo "Success"
  else
    echo "Failed"
  fi
}

# register the cleanup function to be called on the EXIT signal
trap workdir_cleanup EXIT