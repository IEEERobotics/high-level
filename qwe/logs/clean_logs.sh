#/usr/bin/env bash

name="unittests $(echo $(date) | tr ":" ".").tar"
tar -cf "$name" unittests.log*
mv "$name" arch/
rm -f unittests*
