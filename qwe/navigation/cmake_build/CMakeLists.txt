cmake_minimum_required(VERSION 2.4.6)
set(CMAKE_BUILD_TYPE Release)
include_directories(${PROJECT_SOURCE_DIR}/code)

add_library(sbpl
  ../src/discrete_space_information/navxythetalat/environment_navxythetalat.cpp
  ../src/planners/ARAStar/araplanner.cpp
  ../src/planners/ADStar/adplanner.cpp
  ../src/planners/VI/viplanner.cpp
  ../src/planners/PPCP/ppcpplanner.cpp
  ../src/planners/RStar/rstarplanner.cpp
  ../src/planners/ANA/ANAplanner.cpp
  ../src/utils/heap.cpp
  ../src/utils/mdp.cpp
  ../src/utils/utils.cpp
  ../src/utils/2Dgridsearch.cpp
  )

# Build executables in the bin directory
set(EXECUTABLE_OUTPUT_PATH ${PROJECT_SOURCE_DIR}/bin)
