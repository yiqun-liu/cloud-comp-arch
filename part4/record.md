# Experiments Command Records

setup the cluster (see handouts)

upload scripts

```shell
# copy controller and schedulers to memcached server nodes
scp -i ~/.ssh/cloud-computing controller/*.py ubuntu@external_ip:~
# copy initialization scripts to client nodes (measurement, client)
scp -i ~/.ssh/cloud-computing init-clients.sh ubuntu@external_ip:~
```

ssh onto servers

```shell
gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@machine_name
```

## Deploy Memcached Server

### Install Memcached

```shell
sudo apt update
sudo apt install -y memcached libmemcached-tools
sudo vim /etc/memcached.conf
# 1) add '-t 2'
# 2) '-m 64' -> '-m 1024'
# 3) '-l 127.0.0.1' -> '-l $internal_machine_ip'
sudo systemctl restart memcached
# check whether the daemon process is healthy, and make sure all arguments are right
sudo systemctl status memcached
```

### Install Python Docker SDK

```shell
sudo apt-get install python3-pip
pip3 install docker
sudo usermod -a -G docker ubuntu
```

## Deploy Memcached Clients

```shell
# machine: client-agent, client-measurement
sudo bash ~/init-clients.sh
# client-agent
~/memcache-perf-dynamic/mcperf -T 16 -A
# client-measure (remember to run this every time you restart memcached server)
~/memcache-perf-dynamic/mcperf -s INTERNAL_MEMCACHED_IP --loadonly
```

## Run Test

Run batch workloads

```shell
# memcached server side
sudo python3 single_task_scheduler.py
```

Run memcached requests (`mcperf`) and pipe the outputs to a file for later inspection.

