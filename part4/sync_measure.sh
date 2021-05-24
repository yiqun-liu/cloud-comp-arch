#!/bin/bash
# this script accepts three positional arguments:
# 1) test-name: the results will be written to test-name.txt
# 2) memcached-server-ip
# 3) memcached-agent-ip

if [ -z $1 ] || [ -z $2 ] || [ -z $3 ]
then
    echo "Please provide all three positional arguments: 1)test-name, 2)server-ip and 3)agent-ip."
    exit 1
else
    echo "test-name = $1"
    echo "memcached-server-ip = $2"
    echo "memcached-agent-ip = $3"
fi

timeToWholeMin=$((60-$(date +%S)))

# when remaining time is less than 10 secs, we ask user to postpone the start of monitoring
if [ $timeToWholeMin -lt 10 ]
then
    echo 'Please do not start monitoring until further notice.'
    sleep $timeToWholeMin
    echo 'Please start monitoring within a minute.'
    sleep $((60-$(date +%S)))
else
    echo "Please start monitoring within $timeToWholeMin seconds."
    sleep $((60-$(date +%S)))
fi

# put measuring commands here
~/memcache-perf-dynamic/mcperf -s $2 -a $3 \
    --noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 5 \
    --scan 5000:100000:5000 >> ${1}.txt

echo 'sync measure done.'
