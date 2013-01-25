#!/bin/bash
# Checks current IP address on a particular interface using ifconfig.

iface=${1:-eth0} # default interface is eth0
ifconfig $iface | sed -n '/inet /{s/.*addr://;s/ .*//;p}'
