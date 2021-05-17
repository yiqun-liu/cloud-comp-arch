# Resource Monitor

A python tool useful for part 3 & 4 of the project.

## Dependencies

* Python 3
* psutil

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

