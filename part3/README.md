# Static Batch Workload Scheduling

## Motivation

Decouple scheduling policy design and operating works on Kubernetes cluster. Scheduling could be fully specified in a `yaml` file. The scripts load in the scheduling, and carry out experiment automatically.

## Dependencies

The scripts have been validated with
* Python 3.8
* PyYAML 0.2.5

You might want to run `conda install pyyaml` or `pip3 install pyyaml` first.

## Usage

```shell
# <schedule-yaml-file>: the yaml file which specifies the ordering of eahc batch workload
# <parsec-workloads-spec>: the Kubernetes-oriented specification of parsec-workloads (which we used in part2 of the project)
python poll-label.py <schedule-yaml-file-path> <parsec-workloads-spec-dir>
python poll-submit.py <schedule-yaml-file-path> <parsec-workloads-spec-dir>
# example
python poll-submit.py example-schedule.yaml local/fake/
```

`poll-label.py` and `poll-submit.py` are slightly different in their triggering policies:

* `poll-label.py` submits all jobs at once, polls the states of each job, and add labels to worker nodes accordingly. Each job would only be scheduled to nodes with the completion label of its predecessor. Therefore the scheduling decision is only made after label changes.
* `poll-submit.py` is more intuitive: polls the state of running jobs, and submit a job only when all its predecessors have completed.

In both cases, polling observations are done our local computer which runs the script (rather than a component of K8S cluster). I expect they have similar performance.

## Scheduling

`example-schedule.yaml` serves as a self-explanatory template.

