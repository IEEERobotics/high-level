#!/usr/bin/env bash

cd ./cmake_build
cmake CMakeLists.txt
cmake_return=$?
make
make_return=$?
cd ..
time ./cmake_build/bin/test_sbpl ./envs/env1.cfg ./mprim/all_file.mprim
sbpl_return=$?
echo "Output is in $PWD/sol.txt"
diff ./sol.txt ./sols/sol1_gold.txt
diff_return=$?
rm sol.txt envdebug.txt debug.txt
echo $cmake_return $make_return $sbpl_return $diff_return
