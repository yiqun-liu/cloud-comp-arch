import os
import sys
import time
import json
import psutil

# sampling interval, in second
INTERVAL = 5

def get_memcached_pids():
    stream = os.popen('pgrep memcached')
    return stream.read().split()

# synchronous query to shell, returns the list of process-ids for batch workloads
def get_running_workloads():
    stream = os.popen("pgrep 'blackscholes|canneal|dedup|ferret|fft|freqmine'")
    return stream.read().split()

# we need to keep the reference of psutil.Process across invocation, otherwise cpu-utilization could not
# be accurately measured
processes = dict()
def get_resource_utilization(pid):
    global processes
    if pid in processes:
        process = processes[pid]
    else:
        process = psutil.Process(pid)
        processes[pid] = process
    name, sample = process.name(), process.as_dict(attrs=['cpu_affinity', 'cpu_percent', 'num_threads', 'memory_info'])
    sample['rss'] = sample['memory_info'][0]
    sample['timestamp'] = time.time()
    del sample['memory_info']

    return name, sample

last_length = 0
def print_state(message):
    global last_length
    # return to the left of the line
    sys.stdout.write('\b' * last_length)
    sys.stdout.write(message)
    sys.stdout.flush()
    last_length = len(message)

def main():
    workload_started = False
    # number of consecutive empty samples observed
    num_empty, num_samples = 0, 0

    # stop monitoring when after we cannot sample useful information twice
    records = dict()
    memcached_pids = get_memcached_pids()
    while not workload_started or num_empty < 2:
        # sampling
        pids = get_running_workloads()
        for pid in pids + memcached_pids:
            name, sample = get_resource_utilization(int(pid))
            if name in records:
                records[name].append(sample)
            else:
                records[name] = [sample]

        # update state
        num_samples += 1
        if len(pids) > 0:
            workload_started = True
            num_empty = 0
        else:
            num_empty += 1

        # output progress
        state = 'RECORD' if workload_started else 'WAIT'
        message = '{}: {} / {}'.format(state, num_empty, num_samples)
        print_state(message)

        # sleep
        time.sleep(INTERVAL)

    # write to file
    file_name = time.strftime('%m%d-%H%M.json')
    with open(file_name, 'w') as f:
        json.dump(records, f)
    print('\nRecords have been written to {}.'.format(file_name))

if __name__ == '__main__':
    main()

