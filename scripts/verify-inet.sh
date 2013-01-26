#!/bin/bash
# Recursively waits for the internet connection to come up, pinging a specified host to verify.

maxIter=${1:-3} # number of tries before aborting
loopDelay=${2:-10} # seconds
targetHost=people.engr.ncsu.edu # whom to ping

verifyInet() {
  for (( i=1; i<=$maxIter; i++ ))
  do
    ping -c1 $targetHost > /dev/null
    if [ "$?" -eq 0 ] # ping returns 0 if successful
    then
      echo "Internet OK.";
      exit 0
    else
      echo "Internet unavailable...";
      if [ $i -lt $maxIter ]
      then
        sleep $loopDelay
      fi
    fi
  done
  
  echo "Aborted after $maxIter tries.";
  exit 1
}

verifyInet
