import os
import sys
import time

from utilities import jobs, remove_null, node_types, remove_all_labels, get_node_name, load_yaml, save_yaml, \
    submit_job, get_completed_list, add_complete_label, remove_all_jobs

# decided at run time
# code we used in schedule config file (2c, 4c, 8c) -> kubernetes node name
code_node = dict()
# job -> node name
job_node = dict()

def transform(schedule, base_config):
    # sanity check and preprocess
    assert schedule['job'] in jobs
    for j in schedule['follows']:
        assert j in jobs
    remove_null(schedule)

    # some useful reference
    config = base_config
    spec = config['spec']['template']['spec']
    if 'nodeSelector' not in spec:
        spec['nodeSelector'] = dict()
    node_selector = spec['nodeSelector']
    container_config = spec['containers'][0]
    cmd_args = container_config['args']

    # --- location ---
    # node: override
    if 'cca-project-nodetype' in node_selector:
        del node_selector['cca-project-nodetype']
    if schedule['node'] == '2c':
        node_selector['cca-project-nodetype'] = node_types[0]
    elif schedule['node'] == '4c':
        node_selector['cca-project-nodetype'] = node_types[1]
    elif schedule['node'] == '8c':
        node_selector['cca-project-nodetype'] = node_types[2]
    else:
        raise ValueError('node type error for {}.'.format(schedule['job']))
    job_node[schedule['job']] = code_node[schedule['node']]

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
            assert cmd_args[1][-4:] == '-n 1'
            cmd_args[1] = cmd_args[1][:-1] + str(num_threads)

    # --- order ---
    for to_wait in schedule['follows']:
        node_selector[to_wait] = 'done'

    return config

def main(schedule_path, base_config_dir, output_dir):
    remove_all_jobs()
    remove_all_labels()
    # get node names
    code_node['2c'] = get_node_name('node-a-2core')
    code_node['4c'] = get_node_name('node-b-4core')
    code_node['8c'] = get_node_name('node-c-8core')

    # paths of job spec yaml
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
        submit_job(output_path)

    # used to differentiate already-completed jobs and newly completed jobs
    completed = list()
    while len(completed) < 6:
        new_completed = get_completed_list()
        for job in new_completed:
            if job in completed:
                continue

            job_name = job[7:]
            print('Job {} completed.'.format(job_name))
            add_complete_label(job_node[job_name], job_name)
        completed = new_completed
        time.sleep(2)

    print('All completed.')

if __name__ == '__main__':
    schedule_path = sys.argv[1]
    schedule_name = os.path.basename(schedule_path)
    schedule_name = os.path.splitext(schedule_name)[0]

    base_config_dir = sys.argv[2]

    output_dir = '/tmp/poll-label/' + schedule_name
    os.makedirs(output_dir, exist_ok=True)

    main(schedule_path, base_config_dir, output_dir)
