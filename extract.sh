#!/bin/bash

usage()
{
  echo "Usage: extract.sh <firmware> <output folder [default: ./unpacked/]>"
  echo "Usage: extract.sh umount <output folder [default: ./unpacked/]>"
  exit 1
}

main()
{
  local UNPACK_DIR="unpacked"

  if [ $# -lt 1 ]; then
    usage
  fi

  local FIRMWARE=$1
  if [ $# -ge 2 ]; then
    UNPACK_DIR=$2
  fi

  if [ "$1" = "umount" ]; then
    cd "$UNPACK_DIR"
    for file in *.img; do
      folder="${file%%.*}"
      sudo umount "${folder}"
    done
    cd ..
    exit 0
  fi

  python3 unpack.py "$FIRMWARE" "$UNPACK_DIR"

  cd "$UNPACK_DIR"
  for file in *.img; do
    folder="${file%%.*}"
    mkdir "${folder}"
    sudo mount "${file}" "${folder}" -o loop
  done
  cd ..
}

main $*

