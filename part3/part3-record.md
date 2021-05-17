# Experiment Commands Records

transfer monitor scripts 

```shell
# copy resource_monitor to worker nodes (2c, 4c, 8c)
scp -i ~/.ssh/cloud-computing resource_monitor.py ubuntu@external_ip:~
# copy initialization scripts to client nodes
scp -i ~/.ssh/cloud-computing init-clients.sh ubuntu@external_ip:~
```

## Deploy Memcached

deploy memcached server

```shell
# local machine
kubectl create -f memcache-t1-cpuset.yaml
kubectl expose pod some-memcached --name some-memcached-11211 \
    --type LoadBalancer --port 11211 --protocol TCP
# remember memcached IP address (different from external IP of the node)
kubectl get service some-memcached-11211
kubectl get pods -o wide
```

ssh into client & measurement machiens and compile memcached clients

```shell
# machine: client A, client B, measurement machine
sudo chmod +x ~/init-clients.sh
sudo ~/init-clients.sh
```

## Start Memcached Queries

start memcache clients 

```shell
# machine: client A
~/memcache-perf/mcperf -T 2 -A
# machine: client B
~/memcache-perf/mcperf -T 4 -A
# machine: client-measure - load data
~/memcache-perf/mcperf -s $MEMCACHED_IP --loadonly
```

prepare query scrpts

```shell
# run-test.sh at measure machine
date +%s
~/memcache-perf/mcperf -s $MEMCACHED_IP -a $INTERNAL_AGENT_A_IP -a $INTERNAL_AGENT_B_IP \
    --noload -T 6 -C 4 -D 4 -Q 1000 -c 4 -t 20 \
    --scan 30000:30500:10
```

run queries and direct the output to a log file

```shell
bash run-test.sh > s1-measure.txt
```

## Deploy Resource Utilization Monitor

install dependencies

```shell
# machine: node a, b and c
sudo apt-get install python3-pip
pip3 install psutil
```

start monitoring (however, the scripts should be started only after memcached server has been deployed)

```shell
python3 resource_monitor.py
```

## Submit Batch Workloads

```shell
# local machine
python poll-submit.py schedules/s1.yaml ../parsec-native/
```

## Collect Data

```shell
# local machine: save K8S job info
kubectl get jobs > s1-local.txt
# worker nodes (2C, 4C, 8C): save resource utilization information
scp -i ~/.ssh/cloud-computing ubuntu@external_ip:~/*.json .
# memcached-measurement: save latency information
scp -i ~/.ssh/cloud-computing ubuntu@external_ip:~/*.txt .
```

## Visualize Data

visualize resource utilization

```shell
python plot-resource.py $JSON_LOG_DIR $SCHEDULE_NAME
# e.g. python plot-resource.py ../logs s1
```

visualize time slots

TODO