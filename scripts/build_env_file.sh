#!/usr/bin/env bash
# Example call: Usage: ./build_env_file.sh <start_x> <start_y> <start_theta> <end_x> <end_y> <end_theta> [<env_file> <map_file>]

# Confirm that correct number of params were given
if [ $# -ne 6 -a $# -ne 8 ]
then
  echo "Usage: ./build_env_file.sh <start_x> <start_y> <start_theta> <end_x> <end_y> <end_theta> [<env_file> <map_file>]"
  exit 1
fi

# Read in start and end poses from call params
start_x=$1
start_y=$2
start_theta=$3
end_x=$4
end_y=$5
end_theta=$6

if [ $# -eq 6 ]
then
  # File and directory locations not given, assume being called from ./scripts
  echo "Using default files"
  ENV_FILE="../qwe/navigation/envs/env.cfg"
  MAP_FILE="../qwe/navigation/maps/binary_map.txt"
fi

if [ $# -eq 8 ]
then
  # File and directory locations given by caller
  ENV_FILE=$7
  MAP_FILE=$8
fi

# Constant environment configuration vars
obsthresh=1
cost_inscribed_thresh=1
cost_possibly_circumscribed_thresh=0
cellsize=0.025 # Meters TODO This is a fake value
nominalvel=1.0 # Meters per second TODO This is a fake value
timetoturn45degsinplace=2.0 # Seconds TODO This is a fake value

# Get size of course in cells
y_len=$(cat $MAP_FILE | tr -cd "01\n" | wc -l)
total_bytes=$(cat $MAP_FILE | tr -cd "01" | wc -c)
x_len=$(expr $total_bytes / $y_len)

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
