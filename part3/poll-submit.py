import os
import sys
import time

from utilities import jobs, node_types, remove_null, load_yaml, save_yaml, submit_job, get_completed_list, \
    remove_all_jobs


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

    return config

def main(schedule_path, base_config_dir, output_dir):
    remove_all_jobs()

    # order-info: job -> number number of jobs to wait; job -> [jobs waiting for this job]
    wait, notify = dict(), dict()
    for job in jobs:
        wait[job] = 0
        notify[job] = list()

    # number of jobs already submitted
    submitted = 0
    # paths of job spec yaml
    paths = dict()
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
        if 'follows' in schedule and len(schedule['follows']) > 0:
            for to_wait in schedule['follows']:
                wait[job] += 1
                notify[to_wait].append(job)
            paths[job] = output_path
        else:
            submit_job(output_path)
            submitted += 1

    # used to differentiate already-completed jobs and newly completed jobs
    completed = list()
    while submitted < 6:
        new_completed = get_completed_list()
        for job in new_completed:
            if job in completed:
                continue

            # notify jobs which are waiting for this newly completed job
            for j in notify[job[7:]]:
                wait[j] -= 1
                if wait[j] == 0:
                    submit_job(paths[j])
                    submitted += 1
        completed = new_completed
        time.sleep(2)

    print('All submitted.')

if __name__ == '__main__':
    schedule_path = sys.argv[1]
    schedule_name = os.path.basename(schedule_path)
    schedule_name = os.path.splitext(schedule_name)[0]

    base_config_dir = sys.argv[2]

    output_dir = '/tmp/poll-submit/' + schedule_name
    os.makedirs(output_dir, exist_ok=True)

    main(schedule_path, base_config_dir, output_dir)
