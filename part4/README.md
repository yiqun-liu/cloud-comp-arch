# Dynamic Resource Allocation and Workload Scheduling

## Scripts

These scripts are for testing environment set-ups:

* `init-clients.sh`: install `mcperf` on "client" and "measurement" VMs.
* `sync-measure.sh`: run mcperf test at next whole minutes.



## Controllers and Schedulers

Batch workload scheduling is done by two components: controller and scheduler.

The controller passes control to the scheduler periodically, and it offers scheduler:

* handlers of memcached / batch workload, such that scheduler can adjust resource allocation, start / pause workload execution
* necessary information to make scheduling decisions, e.g. CPU utilization

Controller hides the complexity of docker API, system utilization sampling and loggings and provides a neat interface. This allows us to focus on scheduling logic and explore various scheduling strategies efficiently.

Our schedulers are implemented in an imperative way, and is not very neat as a result of quick development. In `main` function, a controller suits its need is instantiated, and the execution is started. To test any scheduler, just run `${scheduler_name}.py`.



## Best Scheduler

The best scheduler we have is `s6.py`
