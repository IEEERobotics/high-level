#!/usr/bin/bash
for image in $@
do
	echo $image
	Debug/CVSandbox.exe $image
	echo
done
