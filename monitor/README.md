# Resource Utilization Monitor

* `resource_monitor.py`: a python tool useful for part 3 & 4 of the project. Resource utilization of batch workload and memcached is computed at fixed, preset period.
* `basic_monitor.py`: a python tool which periodically sampels utilization related stats, useful for part4 of the project. It is intended for oversampling: the interval of interest is decided by `mcperf` running on another VM, and we only have access to that piece of information in post-processing.

## Dependencies

`resource_monitor.py`:

* Python 3
* psutil

`basic_monitor.py`: only Python3 is required.

## Usage

`scp` the script to the server
```shell
scp -i ~/.ssh/cloud-computing resource_monitor.py ubuntu@<MACHINE_NAME>:~
```

ssh into the machine
```shell
cloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@<MACHINE_NAME> \
                  --zone europe-west3-a
```

### Resource Monitor

install dependencies. start the workload before batch workload is initiated, but after memcached server process is started.

```shell
# install dependencies
sudo apt-get install python3-pip
pip3 install psutil

# start memcached (omitted)

# start monitoring
python resource_monitor.py

# initiate memcached request & start batch workload (omitted)
```

The script will automatically terminate if batch workload processes could no longer be observed for a certain period of time.

### Basic Monitor

Basic monitor is a monitor specifically designed for part4, question 2. It cares only about memcached process, and should started when memcached daemon process is up. In addition, user need to provide observing time in seconds. For question 2, `180` is sufficient.

To synchronize measurements as much as possible, this script is designed to use together with `sync_measure.sh` (see part4/). Tester should run `sync_measure.sh` first, see its instruction and start `basic_monitor.py` accordingly. This way, the requests and measurements will all start at next nearest whole minute.

```shell
python3 basic_monitor.py 180
```

