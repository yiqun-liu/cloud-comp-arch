import os
import subprocess
import time

import yaml

jobs = ['blackscholes', 'canneal', 'dedup', 'ferret', 'fft', 'freqmine']
node_types = ['node-a-2core', 'node-b-4core', 'node-c-8core']

# remove null-value "subtree" in a dictionary tree
def remove_null(d):
    # copy keys: we need to modify the tree during iteration
    keys = list(d.keys())
    for k in keys:
        if type(d[k]) is dict:
            if len(d[k].keys()) != 0:
                remove_null(d[k])
            if len(d[k].keys()) == 0:
                d.pop(k)
        elif d[k] is None:
            d.pop(k)

def load_yaml(path):
    with open(path, 'r') as f:
        d = yaml.safe_load(f)
    return d

def save_yaml(d, path):
    with open(path, 'w') as f:
        yaml.dump(d, f, sort_keys=False)
        print('file generated: {}.'.format(path))

def get_completed_list():
    # https://kubernetes.io/docs/concepts/overview/working-with-objects/field-selectors/
    stream = os.popen("kubectl get pods --field-selector=status.phase=Succeeded " +
                      "--output=jsonpath='{.items[*].metadata.labels.job-name}'")
    return stream.read().split()

def submit_job(file_path):
    print('submitting job specified in {}.'.format(file_path))
    # run in a parallel process, main python thread is not affected
    subprocess.Popen(['/bin/bash', '-c', 'kubectl create -f ' + file_path])

def add_complete_label(node_name, job_name):
    label = job_name + '=done'
    print('Add label {} to its node {}.'.format(label, node_name))
    command = 'kubectl label nodes {} {}'.format(node_name, label)
    print(command)
    subprocess.Popen(['/bin/bash', '-c', command])

def remove_all_labels():
    print('remove all previous labels\n' + '-' * 20)
    processes = list()
    for job in jobs:
        processes.append(subprocess.Popen(['/bin/bash', '-c',
                                           'kubectl label nodes --all {}-'.format(job)]))
    # wait until all labels are successfully removed
    for process in processes:
        process.communicate()
    print('-' * 20 + '\nall labels removed\n')

def remove_all_jobs():
    print("remove all jobs in the cluster.")
    stream = os.popen('kubectl delete jobs --all')
    print(stream.read())

    # this line is added according to LIU's debugging experience
    # leave some time for so that our script will not be affected by stale K8S caches
    time.sleep(5)

def get_node_name(node_type):
    stream = os.popen("kubectl get nodes --selector=cca-project-nodetype=" + node_type +
                      " --output=jsonpath='{.items[*].metadata.name}'")
    return stream.read()
