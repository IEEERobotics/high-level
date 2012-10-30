#!/usr/bin/bash
# A simple batch execution script.
# Usage:
#	./run-batch.sh <image file(s)>
# e.g.:
#	./run-batch.sh ~/data/mini-arena-set02/*.png

EXE=Debug/CVSandbox.exe # location of the binary/executable file

for image in $@
do
	echo $image
	$EXE $image
	echo
done
