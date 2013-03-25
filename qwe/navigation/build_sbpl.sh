#!/usr/bin/env bash
# 

if [ $# -ne 1 ]
then
  cd ./cmake_build &> /dev/null
  cd_return=$?
  if [ $cd_return -ne "0" ]
  then
    cd ./navigation/cmake_build &> /dev/null
    cd2_return=$?
    if [ $cd2_return -ne "0" ]
      then
        echo "Error: failed to CD to build dir. Pass as param or run from qwe or qwe/navigation."
        exit 1
    fi
  fi
else
  path_to_build_dir=$1
  cd $path_to_build_dir
  cd3_return=$?
  if [ $cd3_return -ne "0" ]
    then
      echo "Error: failed to CD to build dir. Pass as param or run from qwe or qwe/navigation."
      exit 1
  fi
fi

# Run cmake and check result
cmake CMakeLists.txt &> /dev/null
cmake_return=$?
if [ $cmake_return -ne "0" ]
then
  echo "Error: cmake returned exit code" $cmake_return
  exit 1
fi

# Run make and check result
make &> /dev/null
make_return=$?
if [ $make_return -ne "0" ]
then
  echo "Error: make returned exit code" $cmake_return
  exit 1
fi
