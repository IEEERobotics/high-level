#!/usr/bin/env python

DISCRETIZATION = 15 # Cells
OBSTHRESH = 1
COST_INSCRIBED_THRESH = 1
COST_POSSIBLY_CIRCUMSCRIBED_THRESH = 0
CELLSIZE = 0.025 # Meters
NOMINALVEL = 1.0 # Meters per second
TIMETOTURN45DEGSINPLACE = 2.0 # Seconds
ENVIROMENT = \
"0 0 0 0 0 0 1 1 0 0 0 0 0 0 0  " + "\r\n" \
+ "0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 1 1 0 0 0 0 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 1 1 1 1 0 0 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n" \
+ "1 1 1 1 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n" \
+ "1 1 1 1 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n" \
+ "0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 " + "\r\n"

def genEnvTestFile(currentPose = {'theta': 0, 'x': 0.11, 'y': 0.11}, goalPose = {'theta': 0, 'x': 0.35, 'y': 0.3}):
  """Builds a file suitable as input for SBPL. Eventually, params will be passed directly to SBPL, not written out.

  :param goalPose: X, Y and theta of the desired bot location
  """
  # Open enviroment file for writing
  envFile = open("navigation/envs/envTestFile.cfg", "w")

  # Write configuration to environment file
  envFile.write("discretization(cells): " + str(DISCRETIZATION) + " " + str(DISCRETIZATION) + "\r\n"
    + "obsthresh: " + str(OBSTHRESH) + "\r\n"
    + "cost_inscribed_thresh: " + str(COST_INSCRIBED_THRESH) + "\r\n"
    + "cost_possibly_circumscribed_thresh: " + str(COST_POSSIBLY_CIRCUMSCRIBED_THRESH) + "\r\n"
    + "cellsize(meters): " + str(CELLSIZE) + "\r\n"
    + "nominalvel(mpersecs): " + str(NOMINALVEL) + "\r\n"
    + "timetoturn45degsinplace(secs): " + str(TIMETOTURN45DEGSINPLACE) + "\r\n"
    + "start(meters,rads): " + str(currentPose["x"]) + " " + str(currentPose["y"]) + " " + str(currentPose["theta"]) + "\r\n"
    + "end(meters,rads): " + str(goalPose["x"]) + " " + str(goalPose["y"]) + " " + str(goalPose["theta"]) + "\r\n"
    + "environment:" + "\r\n" + str(ENVIROMENT))

  # Close environment file
  envFile.close()

if __name__ == "__main__":
  genEnvTestFile()
