echo $1
~/memcache-perf-dynamic/mcperf -s 10.156.0.52 -a 10.156.0.53 \
	--noload -T 16 -C 4 -D 4 -Q 1000 -c 4 -t 30 \
	--scan 30000:90000:30000 >> ${1}.txt
