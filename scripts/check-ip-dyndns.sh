#!/bin/bash
# Checks current *internet-facing* IP address using DynDNS's checkip service.

wget -q -O - checkip.dyndns.org | grep -Eo [0-9]\{1,3\}\\.[0-9]\{1,3\}\\.[0-9]\{1,3\}\\.[0-9]\{1,3\}
