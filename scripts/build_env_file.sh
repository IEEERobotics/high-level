#!/usr/bin/env bash
# Example call: Usage: Usage: ./build_env_file.sh <obsthresh> <cost_inscribed_thresh> <cost_possibly_circumscribed_thresh>
# <cellsize> <nominalvel> <timetoturn45degsinplace> <start_x> <start_y> <start_theta> <end_x> <end_y> <end_theta> [<env_file>
# <map_file>]

# Confirm that correct number of params were given
if [ $# -ne 12 -a $# -ne 14 ]
then
  echo "You gave $# arguments, expected 12 or 14"
  echo "Usage: ./build_env_file.sh <obsthresh> <cost_inscribed_thresh> <cost_possibly_circumscribed_thresh> <cellsize> <nominalvel> <timetoturn45degsinplace> <start_x> <start_y> <start_theta> <end_x> <end_y> <end_theta> [<env_file> <map_file>]"
  exit 1
fi

# Read and store call params
obsthresh=$1
cost_inscribed_thresh=$2
cost_possibly_circumscribed_thresh=$3
cellsize=$4 # Meters
nominalvel=$5 # Meters per second
timetoturn45degsinplace=$6 # Seconds
start_x=$7
start_y=$8
start_theta=$9
end_x=${10}
end_y=${11}
end_theta=${12}

if [ $# -eq 12 ]
then
  # File and directory locations not given, assume being called from ./scripts
  echo "Using default files"
  ENV_FILE="../qwe/navigation/envs/env.cfg"
  MAP_FILE="../qwe/navigation/maps/binary_map.txt"
fi

if [ $# -eq 14 ]
then
  # File and directory locations given by caller
  ENV_FILE=${13}
  MAP_FILE=${14}
fi

# Get size of course in cells
y_len=$(cat $MAP_FILE | tr -cd "01\n" | wc -l)
total_bytes=$(cat $MAP_FILE | tr -cd "01" | wc -c)
x_len=$(expr $total_bytes / $y_len)

# Append env information
echo "discretization(cells):" $x_len $y_len > $ENV_FILE 
echo "obsthresh:" $obsthresh >> $ENV_FILE
echo "cost_inscribed_thresh:" $cost_inscribed_thresh >> $ENV_FILE
echo "cost_possibly_circumscribed_thresh:" $cost_possibly_circumscribed_thresh >> $ENV_FILE
echo "cellsize(meters):" $cellsize >> $ENV_FILE
echo "nominalvel(mpersecs):" $nominalvel >> $ENV_FILE
echo "timetoturn45degsinplace(secs):" $timetoturn45degsinplace >> $ENV_FILE
echo "start(meters,rads):" $start_x $start_y $start_theta >> $ENV_FILE
echo "end(meters,rads):" $end_x $end_y $end_theta >> $ENV_FILE
echo "environment:" >> $ENV_FILE

# Append env map
cat $MAP_FILE >> $ENV_FILE
