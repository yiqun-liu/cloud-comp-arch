import os
import subprocess
import yaml

jobs = ['blackscholes', 'canneal', 'dedup', 'ferret', 'fft', 'freqmine']
node_types = ['node-a-2core', 'node-b-4core', 'node-c-8core']
# decided in run time
node_names = dict()

# we use null in our scheduler merely as placeholder
def remove_null(d):
    keys = list(d.keys()) # copied
    for k in keys:
        if type(d[k]) is dict:
            if len(d[k].keys()) != 0:
                remove_null(d[k])
            if len(d[k].keys()) == 0:
                d.pop(k)
        elif d[k] is None:
            d.pop(k)

def transform(schedule, base_config):
    # sanity check and preprocess
    assert schedule['job'] in jobs
    for j in schedule['follows']:
        assert j in jobs
    remove_null(schedule)

    # some useful reference
    config = base_config
    node_selector = config['spec']['template']['spec']['nodeSelector']
    container_config = config['spec']['template']['spec']['containers'][0]
    cmd_args = container_config['args']

    # --- location ---
    # node: override
    del node_selector['cca-project-nodetype']
    if schedule['node'] == '2c':
        node_selector['cca-project-nodetype'] = node_types[0]
    elif schedule['node'] == '4c':
        node_selector['cca-project-nodetype'] = node_types[1]
    elif schedule['node'] == '8c':
        node_selector['cca-project-nodetype'] = node_types[2]
    else:
        raise ValueError('node type error for {}.'.format(schedule['job']))

    # core: taskset
    if len(schedule['cores']) != 0:
        cores_arg = ','.join([str(c) for c in schedule['cores']])
        core_limiter = 'taskset -c {} '.format(cores_arg)
        cmd_args[1] = core_limiter + cmd_args[1]

    # --- resources ---
    # cpu and memory
    if 'resources' in schedule:
        container_config['resources'] = schedule['resources']

    # threads
    if 'num-threads' in schedule:
        num_threads = schedule['num-threads']
        if num_threads is not None and num_threads > 0:
            assert cmd_args[-4:] == '-n 1'
            cmd_args = cmd_args[:-1] + str(num_threads)

    return config

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
        "--output=jsonpath='{.items[*].metadata.name}'")
    return stream.read().split()

def submit_job(file_path):
    print('submitting job specified in {}.'.format(file_path)
    # run in a parallel process, main python thread is not affected
    subprocess.Popen(['/bin/bash/', 'kubectl create -f ' + file_path])

def main(schedule_path, base_config_dir, output_dir):
    # get node names
    names['2c'] = get_node_name('cca-project-nodetype=node-a-2core')
    names['4c'] = get_node_name('cca-project-nodetype=node-a-4core')
    names['8c'] = get_node_name('cca-project-nodetype=node-a-8core')

    submitted = 0
    paths = dict()
    wait = dict()
    notify = dict()
    for job in jobs:
        wait[job] = 0
        notify[job] = list()
    schedules = load_yaml(schedule_path)
    for schedule in schedules:
        # prepare k8s job yaml
        job = schedule['job']
        file_name = 'parsec-{}.yaml'.format(job)
        input_path = os.path.join(base_config_dir, file_name)
        base_config = load_yaml(input_path)

        config = transform(schedule, base_config)
        output_path = os.path.join(output_dir, file_name)
        save_yaml(config, output_path)

        # create data structure to maintain topological order of submission
        if 'follows' in schedule and len(schedule['follows'):
            for to_wait in schedule['follows']:
                wait[job] += 1
                notify[to_wait].append(job)
                paths[job] = output_path
        else:
            submit_job(output_path)
            submitted += 1

    last_scheduled = list()
    while submitted < 6:
        scheduled = get_scheduled_list()
        for job in scheduled:
            if job in last_scheduled:
                continue
            for j in notify[job[7:]]:
                wait[j] -= 1
                if wait[j] == 0:
                    submit_job(paths[j])
                    submitted += 1
        last_scheduled = scheduled
        time.sleep(2)

    print('All done.')

if __name__ == '__main__':
    schedule_path = 'schedule.yaml'
    schedule_name = os.path.basename(schedule_path)
    schedule_name = os.path.splitext(schedule_name)[0]
    base_config_dir = os.getcwd()
    output_dir = '/tmp/poll/' + schedule_name
    os.makedirs(output_dir, exist_ok=True)
    main(schedule_path, base_config_dir, output_dir)

