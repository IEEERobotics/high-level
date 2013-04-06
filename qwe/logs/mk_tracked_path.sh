#/usr/bin/env bash

cat qwe.log | grep Bot | awk '{print $2,$14,$15,$16}' | head -n -1 > tracked_path.txt
