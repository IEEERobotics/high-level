#!/usr/bin/env bash
# Example call: ./build_env_file.sh start_x start_y start_theta end_x end_y end_theta

# Confirm that correct number of params were given
if [ $# -ne 6 ]
then
  echo "Usage: ./build_env_file.sh start_x start_y start_theta end_x end_y end_theta"
  exit 1
fi

# File and directory locations
MAP_DIR="../qwe/navigation/maps"
ENV_DIR="../qwe/navigation/envs"
ENV_FILE="env.txt"
MAP_FILE="binary_map.txt"

# Constant environment configuration vars
obsthresh=1
cost_inscribed_thresh=1
cost_possibly_circumscribed_thresh=0
cellsize=0.0015875 # Meters TODO Need to confirm that default cell size is 1/16 in
nominalvel=1.0 # Meters per second TODO This is a fake value
timetoturn45degsinplace=2.0 # Seconds TODO This is a fake value

# Get size of course in cells
y_len=$(cat $MAP_DIR/$MAP_FILE | tr -cd "01\n" | wc -l)
total_bytes=$(cat $MAP_DIR/$MAP_FILE | tr -cd "01\n" | wc -c)
x_len=$(expr $total_bytes / $y_len)

# Read in start and end poses from call params
start_x=$1
start_y=$2
start_theta=$3
end_x=$4
end_y=$5
end_theta=$6

echo "discretization(cells):" $x_len $y_len > $ENV_DIR/$ENV_FILE 
echo "obsthresh:" $obsthresh >> $ENV_DIR/$ENV_FILE
echo "cost_inscribed_thresh:" $cost_inscribed_thresh >> $ENV_DIR/$ENV_FILE
echo "cost_possibly_circumscribed_thresh:" $cost_possibly_circumscribed_thresh >> $ENV_DIR/$ENV_FILE
echo "cellsize(meters):" $cellsize >> $ENV_DIR/$ENV_FILE
echo "nominalvel(mpersecs):" $nominalvel >> $ENV_DIR/$ENV_FILE
echo "timetoturn45degsinplace(secs):" $timetoturn45degsinplace >> $ENV_DIR/$ENV_FILE
echo "start(meters,rads):" $start_x $start_y $start_theta >> $ENV_DIR/$ENV_FILE
echo "end(meters,rads):" $end_x $end_y $end_theta >> $ENV_DIR/$ENV_FILE
echo "environment:" >> $ENV_DIR/$ENV_FILE

# Append env map
cat $MAP_DIR/$MAP_FILE >> $ENV_DIR/$ENV_FILE
