#!/usr/bin/evn bash
# Posts current IP address as a *message* to a specified URL (PHP script):
#   http://people.engr.ncsu.edu/achakra/apps/message/post.php
# Posted messages can be viewed at:
#   http://people.engr.ncsu.edu/achakra/apps/message/list.php

iface=${1:-eth0} # interface to report IP for (to be used with check-ip.sh only)
myuser=${2:-`uname -n`} # identifier to be posted along with IP address
posturl=http://people.engr.ncsu.edu/achakra/apps/message/post.php # where to send IP address

# Pick one of 3 ways to get IP address(es)
#myip=`hostname -I`
#myip=`check-ip.sh $iface`
myip=`check-ip-dyndns.sh`

# URL-encode IP string (simple encoding: replace spaces, if any) and post it
myip=`echo $myip | sed 's/ /%20/g'`
wget -q -O - $posturl --post-data=quiet=true\&user=$myuser\&message=$myip
