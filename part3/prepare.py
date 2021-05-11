import os
import sys
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

    # --- order ---
    # risk: cannot add label from a pod; scheduler fails to pend the job
    # add label to notify those following this job
    # todo: node names
    label_adder = 'kubectl label nodes {} {}-done=true'.format(
        node_names[schedule['node']], schedule['job'])

    cmd_args[1] = cmd_args[1] + ' ; ' + label_adder

    # wait for previous jobs to complete
    for to_wait in schedule['follows']:
        nodeSelector[to_wait + '-done'] = True

    return config

def load_yaml(path):
    with open(path, 'r') as f:
        d = yaml.safe_load(f)
    return d

def save_yaml(d, path):
    with open(path, 'w') as f:
        yaml.dump(d, f, sort_keys=False)
        print('file generated: {}.'.format(path))

def get_node_name(selector):
    stream = os.popen("kubectl get pods --selector=" + selector +
        " --output=jsonpath='{.items[*].metadata.name}'")
    return stream.read()

def main(schedule_path, base_config_dir, output_dir):
    # get node names
    names['2c'] = get_node_name('cca-project-nodetype=node-a-2core')
    names['4c'] = get_node_name('cca-project-nodetype=node-a-4core')
    names['8c'] = get_node_name('cca-project-nodetype=node-a-8core')

    schedules = load_yaml(schedule_path)
    for schedule in schedules:
        file_name = 'parsec-{}.yaml'.format(schedule['job'])
        input_path = os.path.join(base_config_dir, file_name)
        base_config = load_yaml(input_path)

        config = transform(schedule, base_config)
        output_path = os.path.join(output_dir, file_name)
        save_yaml(config, output_path)
    print('All done.')

if __name__ == '__main__':
    schedule_path = sys.argv[0]
    schedule_name = os.path.basename(schedule_path)
    schedule_name = os.path.splitext(schedule_name)[0]

    base_config_dir = sys.argv[1]

    output_dir = '/tmp/prepare/' + schedule_name
    os.makedirs(output_dir, exist_ok=True)

    main(schedule_path, base_config_dir, output_dir)

